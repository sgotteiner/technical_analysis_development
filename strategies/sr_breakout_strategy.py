"""
His strategy, on HIS setup's lines (owner, 2026-10-08: "if i said i care about a line in the sr
algorithm i want to see the breakout of this line ... a breakout and a retest. and the strategy buys
only after the retest").

From his notes (2026-09-04 setup "BTC flat resistance + bull flag"): "buy on a breakout of the
resistance line (maybe with a retest)"; "It is the rung below the 79,500 the price is standing on,
so it is the stop"; "the next breakout is the previous peak above".

  the line   a resistance on his screen the day before (setup_history: what the S/R algorithm drew)
             - a level, or the trend line when it runs over price
  breakout   a close above that line's zone (modules/events/detectors.breakout, closes in a row)
  retest     THAT line, by the zigzag (retest="zigzag", the default): the first zigzag valley after the
             breakout lands in the line's zone - a real pullback, big enough to be a zigzag point. "such a
             small candle doesnt count" (owner, 2026-10-08). The buy is the day the zigzag confirms that
             valley - the first day it is known. A valley under the zone, or a close under it first, is a
             failed breakout; a valley above the zone never came back - no trade.
             retest="touch": the first candle back into the zone that closes above the line (before)
  still      the broken line must still be on the zigzag the day it buys: the zigzag can replace its
             newest point, and a line it dropped is not traded (2022-09-10 bought off 20,918, gone a day later)
  buy        at the close of the retest day
  stop       the support rung below the broken line, on his screen that day
  target     the next resistance on his screen above the entry; none (all-time high) = no target
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import numpy as np
from modules.events.detectors import breakout

RETEST_WITHIN = 20        # bars after the breakout - a stated guess, a switch
TOUCH_PCT = 1.5           # the page's touch zone around a line (his drawn boxes: +-1.4%)


@dataclass(frozen=True)
class RetestRules:
    closes: int = 1                # closes in a row above the zone that make the breakout
    retest_within: int = RETEST_WITHIN
    with_trend_lines: bool = True  # the down trend line over price is a resistance too
    retest: str = "zigzag"         # zigzag (valley in the zone) | hold (valley in the zone or above it) | touch
    trend: str = "any"             # any | not_down | up - from the trend lines on the buy day (`trend_at`)
    # the broken LEVEL's strength (zigzag_strength.py): "really weak not supported by 2 peaks and valleys
    # only one ... especially comparing to the trend which is 10 times bigger" (owner, 2026-10-08)
    min_touches: int = 1           # zigzag points on the line
    min_share: float = 0.0         # its swing as a share of the trend's size


def _price(line: Dict, bar: int, day: int) -> float:
    """A line's price at `bar`; `day` is the day it was drawn (where its price was given)."""
    if line.get("slope_pct_day") is None:
        return line["price"]
    return line["price"] * (1 + line["slope_pct_day"] / 100) ** (bar - day)


def _resistances(hist: Dict, day: int, close: float, rules: RetestRules) -> List[Dict]:
    lines = hist.get(day, {}).get("lines", [])
    return [l for l in lines if l["price"] > close and ("resistance" in l["role"]
            or (rules.with_trend_lines and l["kind"] == "trend" and "previous" not in l["role"]))]


def _rungs(hist: Dict, day: int, below: float, above: float):
    lines = hist.get(day, {}).get("lines", [])
    under = [_price(l, day, day) for l in lines if _price(l, day, day) < below]
    over = [_price(l, day, day) for l in lines if _price(l, day, day) > above]
    return (max(under) if under else None), (min(over) if over else None)


def _retest(close, high, low, zone, b: int, within: int) -> Optional[int]:
    for r in range(b + 1, min(b + within, len(close) - 1) + 1):
        lo, hi = zone(r)
        if close[r] < lo:
            return None                              # fell back under the zone: a failed breakout
        if low[r] <= hi and close[r] > (lo + hi) / 2:
            return r
    return None


LOOK_FOR_VALLEY = 120     # bars to wait for the zigzag's first valley after a breakout (the trade's own limit)


def _zigzag_retest(points_at, close, zone, b: int, hold: bool = False):
    """The day the zigzag confirms its first valley after the breakout, if that valley is in the zone -
    or, with `hold`, anywhere above the zone's floor: the pullback held over the broken line."""
    for r in range(b + 1, min(b + LOOK_FOR_VALLEY, len(close) - 1) + 1):
        lo, hi = zone(r)
        if close[r] < lo:
            return None, None                         # fell back under the zone: a failed breakout
        valleys = [p for p in points_at(r) if p[1] != 1 and p[0] > b]
        if valleys:
            v = valleys[0]
            return (r, v) if lo <= v[2] and (hold or v[2] <= hi) else (None, None)
    return None, None


def _still_there(hist: Dict, line: Dict, drawn: int, r: int, points_at=None) -> bool:
    """Is the broken line still made by the zigzag the day it buys? A level: a zigzag point still sits
    at its price (the zigzag can replace its newest point). A trend line: still among that day's lines.
    Not "still shown" - a new valley changes which lines are shown, not whether this one exists."""
    want = _price(line, r, drawn)
    if line["kind"] == "level" and points_at is not None:
        return any(abs(p[2] / want - 1) * 100 <= 0.2 for p in points_at(r))
    return any(l["kind"] == line["kind"] and abs(_price(l, r, r) / want - 1) * 100 <= (0.2 if l["kind"] == "level" else 0.5)
               for l in hist.get(r, {}).get("lines", []))


def signals(hist: Dict, close: np.ndarray, high: np.ndarray, low: np.ndarray, rules: RetestRules,
            points_at=None, trend_at=None) -> List[Dict]:
    """`points_at(day)`: the zigzag's points known that day, (bar, kind, price, confirmed) - for retest="zigzag"."""
    out, half = [], TOUCH_PCT / 100
    for d in sorted(hist):
        for line in _resistances(hist, d - 1, close[d - 1], rules):
            zone = lambda bar, ln=line: (_price(ln, bar, d - 1) * (1 - half), _price(ln, bar, d - 1) * (1 + half))
            st = line.get("strength") or {}
            if line["kind"] == "level" and (st.get("touches", 1) < rules.min_touches
                                            or (rules.min_share and (st.get("rel") or 0) < rules.min_share)):
                continue
            if breakout(close, high, low, zone, d, rules.closes) is None:
                continue
            if rules.retest in ("zigzag", "hold"):
                r, valley = _zigzag_retest(points_at, close, zone, d, hold=rules.retest == "hold")
            else:
                r, valley = _retest(close, high, low, zone, d, rules.retest_within), None
            if r is None or not _still_there(hist, line, d - 1, r, points_at):
                continue
            if rules.trend != "any":
                state = trend_at(r)
                if state == "down" or (rules.trend == "up" and state != "up"):
                    continue
            lo, hi = zone(r)
            stop, target = _rungs(hist, r, lo, close[r])
            if stop is None:
                continue
            out.append({"bar": r, "breakout_bar": d, "line": line, "level": _price(line, r, d - 1),
                        "retest": {"bar": valley[0], "price": valley[2]} if valley else {"bar": r, "price": float(low[r])},
                        "retest_kind": rules.retest,
                        "stop": stop, "target": target if target is not None else float("inf"),
                        "why": f"{line['role']} {line['price']:,.0f} broken, retested and held"})
    return out
