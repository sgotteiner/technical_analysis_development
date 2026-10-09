"""
The trend, read at the scale of the move running now (owner, 2026-10-05/06).

His order is price -> the latest peak or valley -> the move from it -> the trend. So the trend is
read from swings the size of THAT move, not from every wiggle of the page's swing size:

  - a swing counts for the trend when it is "the same move" as the one running now - the bound
    the backward search already uses (precedents.SIMILAR_LO), not a new number. "its relative to
    the move" / "moves that are from line to line". At 7% the March 2026 wiggles (74,050 / 76,000
    over 65,618 / 65,000) read as a horizontal trend at 2026-05-15, where he sees "a downtrend
    clearly and price is on a peak in this downtrend";
  - the extreme price is making now counts as the latest peak or valley for the DIRECTION ("latest
    peak or valley, current move from it"), but it is not a peak until price has turned from it,
    so it never carries the line;
  - the line sits over the highs in a down trend and under the lows in an up trend ("up trends
    lines are marked by candle lows meaning below them and downtrend by highs meaning above them"),
    from where the trend began - the first of its run of lower peaks / higher valleys - through
    the confirmed point that keeps every later one on the far side of it.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from business_logic_services.frozen_zigzag import frozen_points
from business_logic_services.precedents import SIMILAR_LO
from business_logic_services.protected_trend import BREAKS, protected_trend
from business_logic_services.line_rules import MOVE_BAND
from business_logic_services.structure_scale import yardstick
from business_logic_services.swing_frame import turning_points_cached
from business_logic_services.trend_state import DOWN, UP, flat_for, last_trend, range_now
from modules.shapes.sr_turning_points import PEAK, VALLEY
from modules.shapes.swing_moves import running_move


def _structure(df: pd.DataFrame, end: int, size: float, cache: Optional[Dict], tp: Optional[Dict] = None):
    """Confirmed points at `size`, plus the extreme of the leg running now as a provisional one."""
    tp = tp if tp is not None else turning_points_cached(df, size, cache)
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx, kinds = list(tp["idx"][known]), list(tp["kind"][known])
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    confirmed = len(idx)
    if idx and idx[-1] + 1 < end:
        seg = slice(idx[-1] + 1, end + 1)
        if kinds[-1] == PEAK:
            j, k = idx[-1] + 1 + int(np.argmin(low[seg])), VALLEY
        else:
            j, k = idx[-1] + 1 + int(np.argmax(high[seg])), PEAK
        if j < end:                                     # price has turned from it, at least a bar
            idx.append(j)
            kinds.append(k)
    idx, kinds = np.array(idx, dtype=int), np.array(kinds, dtype=int)
    prices = np.where(kinds == PEAK, high[idx], low[idx]) if len(idx) else np.array([])
    return idx, kinds, prices, confirmed


def _through(idx, prices, side, a: int, down: bool, poke: float) -> Optional[Dict]:
    """The line from point `a` over the later confirmed highs (down) / under the lows (up), through
    the point that keeps every later one on the far side - allowing a poke through of up to `poke`
    (a level's width): "what if it passes the line a bit i dont wanna raise the line because of
    that" (2026-09-22). At 2023-08-11 the tiny 2022-12-19 valley, 1.4% under his line, was holding
    it at 24,565 against his 29,887."""
    later = [i for i in side if idx[i] > idx[a]]
    if not later:
        return None
    ya = np.log(prices[a])
    ys = np.log([prices[i] for i in later])
    xs = np.array([idx[i] - idx[a] for i in later], dtype=float)
    slopes = (ys - ya) / xs
    def holds(slope):
        gap = (ys - (ya + slope * xs)) * (-1 if down else 1)     # how far each is on the far side
        return bool((gap >= -poke).all())
    order = np.argsort(slopes) if down else np.argsort(slopes)[::-1]   # steepest first
    j = next((j for j in order if holds(slopes[j])), int(np.argmax(slopes) if down else np.argmin(slopes)))
    return {"x1": float(idx[a]), "y1": float(ya), "slope": float(slopes[j]),
            "first": float(idx[a]), "last": float(idx[later[j]]),
            "points": [float(idx[a]), float(idx[later[j]])]}


def _line(idx, kinds, prices, confirmed: int, first_bar: float, down: bool,
          poke: float = 0.0, flat_pct: float = 0.0) -> Optional[Dict]:
    """Over the confirmed highs (down) / under the confirmed lows (up), from where the trend began."""
    kind = PEAK if down else VALLEY
    side = [i for i in range(confirmed) if kinds[i] == kind]
    start = next((n for n, i in enumerate(side) if idx[i] == int(first_bar)), None)
    if start is None:
        return None
    # walk back while the points keep stepping the trend's way: the first of the run is its start
    while start > 0 and ((prices[side[start - 1]] > prices[side[start]]) if down
                         else (prices[side[start - 1]] < prices[side[start]])):
        start -= 1
    # and it began at its extreme: a later valley under the start (or peak over it) means the trend
    # began there - otherwise an up line drawn "under the valleys" from 76,606 has to pass under
    # 74,508 after it and comes out FALLING (2025-07-04)
    extreme = (lambda pts: max(pts, key=lambda i: prices[i])) if down else         (lambda pts: min(pts, key=lambda i: prices[i]))
    a = extreme(side[start:])
    line = _through(idx, prices, side, a, down, poke)
    # The slope: a trend line may not move more in one swing of the structure than "the same level"
    # allows - steeper than that it runs through the pullbacks of ONE leg, not a trend of swings.
    # At 2023-04-21 the March huge candles gave +1.81%/day, 9.0% a swing against 5.4%, and a line
    # 52% over price; "i think the huge candles confused you ... consider integrating slope logic"
    # (2026-10-06). Then the trend began earlier: at the extreme before this start.
    swing = float(np.median(np.diff(idx[:confirmed][-8:]))) if confirmed > 2 else 0.0
    too_steep = lambda ln: (ln is not None and flat_pct > 0 and swing > 0
                            and abs(ln["slope"]) * swing > np.log(1 + flat_pct / 100))
    while too_steep(line):
        # the nearest earlier low under this start (high over it, for a down trend) - the low the
        # leg started from, not the lowest point in all history
        past = [i for i in side if idx[i] < idx[a]
                and (prices[i] > prices[a] if down else prices[i] < prices[a])]
        if not past:
            break
        a = past[-1]
        line = _through(idx, prices, side, a, down, poke) or line
    return line


def _as_state(trend: Optional[Dict], state: Dict, idx, kinds, prices, confirmed: int) -> Dict:
    """The direction from the protected-low state (protected_trend); the line starts at the
    confirmed peak (down) / valley (up) nearest the bar that trend began at."""
    down = state["direction"] == DOWN
    side = [i for i in range(confirmed) if kinds[i] == (PEAK if down else VALLEY)]
    start = min(side, key=lambda i: abs(idx[i] - state["began"])) if side else None
    base = trend or {"peaks": [], "valleys": [], "peak_prices": [], "valley_prices": []}
    return {**base, "direction": state["direction"],
            "role": "resistance" if down else "support", "still_forming": False,
            "start_bar": float(idx[start]) if start is not None else -1.0}


def _previous(idx, kinds, prices, confirmed: int, rng: Dict, now_move: float,
              size: float) -> Optional[Dict]:
    """The trend before the range: "maybe if current is sideways calculate also the previous trend
    which is what was before the first peak or valley in the pipe" (2026-10-07, at 2022-10-14, where
    a three-week range inside the 2022 bear market hid his "clear trend")."""
    first = min(rng["peaks"][0], rng["valleys"][0])
    before = int(np.sum(idx[:confirmed] < first))
    t = last_trend(idx[:before].astype(float), prices[:before], kinds[:before], flat_for(now_move))
    if t is None or t["direction"] not in (DOWN, UP):
        return None
    down = t["direction"] == DOWN
    line = _line(idx, kinds, prices, before, t["peaks"][0] if down else t["valleys"][0], down,
                 poke=np.log(1 + now_move * MOVE_BAND / 100), flat_pct=flat_for(now_move))
    return {**t, **(line or {}), "size": size, "previous": True}


def structural_trend(df: pd.DataFrame, end: int, now_move: float, floor_size: float,
                     cache: Optional[Dict] = None, tp: Optional[Dict] = None,
                     breaks: int = BREAKS) -> Optional[Dict]:
    """The trend at `end`: direction from swings the size of the move, line over / under them.
    `breaks`: how many breaks of the protected low change it (protected_trend); 0 = the window of
    the last peaks and valleys alone (trend_state.last_trend), the rule before 2026-10-08."""
    if now_move <= 0:
        return None
    # rounded so the turning-point cache is shared between nearby dates, not one entry per day
    size = round(max(SIMILAR_LO * now_move / 100, floor_size), 3)
    idx, kinds, prices, confirmed = _structure(df, end, size, cache, tp)
    # inside a range of confirmed peaks and valleys, the range is the trend - an unfinished extreme
    # cannot stretch its ceiling (2026-05-15: 82,850 was not yet a peak, the March top was 76,000)
    inside = range_now(idx[:confirmed].astype(float), prices[:confirmed], kinds[:confirmed],
                       flat_for(now_move), float(df["Close"].iloc[end]))
    if inside is not None:
        return {**inside, "size": size,
                "previous": _previous(idx, kinds, prices, confirmed, inside, now_move, size)}
    trend = last_trend(idx.astype(float), prices, kinds, flat_for(now_move))
    state = protected_trend(df, end, size, cache, breaks) if breaks else None
    if state is not None:
        trend = _as_state(trend, state, idx, kinds, prices, confirmed)
    if trend is None:
        return None
    if trend["direction"] in (DOWN, UP):
        down = trend["direction"] == DOWN
        start = trend.get("start_bar", trend["peaks"][0] if down else trend["valleys"][0])
        line = _line(idx, kinds, prices, confirmed, start, down,
                     poke=np.log(1 + now_move * MOVE_BAND / 100), flat_pct=flat_for(now_move))
        if line is not None:
            trend = {**trend, **line}
    return {**trend, "size": size}


def readable_move(df: pd.DataFrame, end: int, now_move: float, floor_size: float,
                  cache: Optional[Dict] = None) -> float:
    """The move to read the structure at: the move running now, unless that is so big its own
    swings vanish - then the largest scale at which the move still shows two peaks and two valleys
    (what a trend needs to be read). A move too young to show them keeps its own scale.

    At 2024-03 the +77% rally made the scale 54-63%, and the zigzag had nothing from 2024-01-23 to
    2024-03-08 - "sometimes not enough at all" (owner, 2026-10-07)."""
    if now_move <= 0:
        return now_move
    high, low, close = df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy()
    _, start, _ = running_move(turning_points_cached(df, floor_size, cache), high, low, end,
                               float(close[end]), close)
    top = max(SIMILAR_LO * now_move / 100, floor_size)
    size = top
    while size >= floor_size:
        tp = turning_points_cached(df, round(size, 3), cache)
        k = (tp["conf"] <= end) & (tp["idx"] >= start) & (tp["idx"] <= end)
        if (tp["kind"][k] == PEAK).sum() >= 2 and (tp["kind"][k] != PEAK).sum() >= 2:
            return size * 100 / SIMILAR_LO
        size *= 0.9
    return now_move                        # too young to show its swings: its own scale


def read_structure(df: pd.DataFrame, end: int, now_move: float, floor_size: float,
                   cache: Optional[Dict] = None, frozen: bool = False, breaks: int = BREAKS):
    """(the trend, the move everything is measured against) at `end`.

    The structure's own yardstick (structure_scale) only replaces the move running now when it
    finds a RANGE price is inside - his note was about a pipe: "the pipe is about 25% ... 1% lower
    lows ... its noise compared to 25%" (2026-10-06, 2024-08-02). Inside a trend every larger scale
    finds a larger leg: at 2024-01-19 a 13% pullback climbed to the whole 2022-2024 bull leg and
    the "trend" started in 2018 at 6,625. There the move running now stays the ruler."""
    cache = cache if cache is not None else {}
    now_move = readable_move(df, end, now_move, floor_size, cache)
    # the scale is still today's; the peaks and valleys read at it are the frozen ones - decided on
    # the day each was confirmed, so stepping "now" back does not redraw the past (2026-10-07)
    tp = frozen_points(df, end, floor_size, cache) if frozen else None
    yard = yardstick(df, end, now_move, floor_size, cache)
    if yard > now_move:
        wide = structural_trend(df, end, yard, floor_size, cache, tp, breaks)
        if wide is not None and wide.get("inside"):
            return wide, yard
    return structural_trend(df, end, now_move, floor_size, cache, tp, breaks), now_move


def zigzag(df: pd.DataFrame, end: int, size: float, cache: Optional[Dict] = None,
           tp: Optional[Dict] = None) -> list:
    """The zigzag the trend is read from - confirmed peaks and valleys at `size` plus the extreme of
    the leg still forming - to lay beside the one he draws (owner, 2026-10-07: "look how i draw the
    zigzag. i want you to draw it too")."""
    idx, kinds, prices, confirmed = _structure(df, end, size, cache, tp)
    t = df.index
    points = [{"time": int(t[int(i)].timestamp()), "price": float(p)} for i, p in zip(idx, prices)]
    if len(idx) == confirmed and len(idx) and idx[-1] < end:
        # the leg still forming runs on to its extreme so far - even when that is today, which is
        # not yet a peak for the trend (price has not turned) but is where the line has got to:
        # at 2024-03-08 the rally from 2024-01-23 was not drawn at all on a new-high day
        seg = slice(int(idx[-1]) + 1, end + 1)
        high, low = df["High"].to_numpy()[seg], df["Low"].to_numpy()[seg]
        j = int(np.argmax(high) if kinds[-1] != PEAK else np.argmin(low))
        points.append({"time": int(t[int(idx[-1]) + 1 + j].timestamp()),
                       "price": float(high[j] if kinds[-1] != PEAK else low[j])})
    return points
