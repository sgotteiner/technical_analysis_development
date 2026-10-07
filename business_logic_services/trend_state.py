"""
The trend, as he defines it (owner, 2026-10-05):

  "i want a last trend line which is the last line with at least 2 peaks and valleys at changing
   levels. it possible we already broke it and dont have 2 peaks and valleys yet so we didnt change
   the trend yet ... if it horizontal thats a trend too."

So a trend is read off the STRUCTURE, not fitted to points:

  up          the last two peaks are higher AND the last two valleys are higher
  down        both lower
  horizontal  both at the same level - a range is a trend too
  unchanged   when the newest pair says nothing, the window widens one pair at a time (up to
              WIDEST) - breaking a trend does not make a new one until two peaks and two valleys
              say so. "The same level" is a step smaller than a share of the MOVE, never a
              percentage: "no flat magic numbers ... compare it to the move size."

ONE line comes out of it - the one price is working against: the peaks in a downtrend, the valleys
in an up trend, and in a range the side price is nearer. Not a million lines.
"""
from typing import Dict, List, Optional
import numpy as np

PEAK = 1
UP, DOWN, FLAT = "up", "down", "horizontal"


def _direction(a: float, b: float, flat_pct: float) -> str:
    """Where b sits against a: higher, lower, or the same level."""
    change = (b / a - 1) * 100
    if change > flat_pct:
        return UP
    if change < -flat_pct:
        return DOWN
    return FLAT


WIDEST = 4          # how far back the window may widen before the answer is "horizontal"


def _all_level(prices, idxs, flat_pct: float) -> bool:
    """Are all of these at one height - the top of a range, or its floor?"""
    if len(idxs) < 2:
        return False
    vals = [prices[i] for i in idxs]
    return (max(vals) / min(vals) - 1) * 100 <= flat_pct


def _pairs_at(bars, prices, kinds, upto: int, n: int = 2):
    """The last n peaks and the last n valleys at or before index `upto`."""
    peaks = [i for i in range(upto + 1) if kinds[i] == PEAK]
    valleys = [i for i in range(upto + 1) if kinds[i] != PEAK]
    return peaks[-n:], valleys[-n:]


FLAT_SHARE = 0.45       # a step smaller than this much of the move running now is "the same level"


def flat_for(now_move: float) -> float:
    """How far apart two peaks may be and still be at the same level - as a share of the MOVE,
    never a percentage. "flat 2% what if we traded scalping? the threshold will be meaningless.
    its relative to the move. no flat magic numbers" (owner, 2026-10-05).

    Bounded by his own dates, not chosen: at 2026-04-10 he reads a horizontal with steps of 0.35
    and 0.34 of the move, so flat has to reach 0.35; at 2026-09-04 he reads an up trend with steps
    of 0.62 and 0.57, so it has to stop below 0.57. This sits between them.
    """
    return max(now_move, 0.0) * FLAT_SHARE


def last_trend(bars: np.ndarray, prices: np.ndarray, kinds: np.ndarray,
               flat_pct: float = 2.0) -> Optional[Dict]:
    """The last trend two peaks and two valleys agree on, walking back until they do.

    `flat_pct` comes from `flat_for(move running now)`: the caller passes the move, not a constant.
    """
    if len(bars) < 4:
        return None
    upto = len(bars) - 1
    # Two peaks and two valleys first; if they do not say anything, look one pair further back,
    # up to WIDEST. His own four dates need this: at 2026-02-13 the last two peaks are 1.5% apart
    # (nothing), while three of them run 97,924 -> 72,271 and the trend is plainly down. If nothing
    # changes across the widest window, the structure IS horizontal - "if it horizontal thats a
    # trend too" (owner, 2026-10-05).
    chosen = None
    for n in range(2, WIDEST + 1):
        peaks, valleys = _pairs_at(bars, prices, kinds, upto, n)
        if len(peaks) < n or len(valleys) < n:
            break
        pk = _direction(prices[peaks[0]], prices[peaks[-1]], flat_pct)
        vl = _direction(prices[valleys[0]], prices[valleys[-1]], flat_pct)
        if pk == vl and pk != FLAT:
            chosen = (pk, peaks, valleys)
            break
        # no early exit on "both flat": two peaks at one level may still be a pause inside a trend.
        # Only when the WIDEST window still shows nothing is the structure really horizontal.
        # A range price is still INSIDE is caught before this, by range_now.
    if chosen is None:
        # Nothing changed in any window. Two different situations, and he separates them:
        # "if its a horizontal move with same hight peaks and valley ok but if not you need to find
        # the last trend that had it" (2026-10-05).
        peaks, valleys = _pairs_at(bars, prices, kinds, upto, 2)
        if _all_level(prices, peaks, flat_pct) and _all_level(prices, valleys, flat_pct):
            chosen = (FLAT, peaks[-2:], valleys[-2:])     # a real range: that is a trend
        else:
            # the peaks and valleys disagree - one higher peak after a down trend does not make an
            # up trend. Step back and report the last trend that WAS established.
            older = last_trend(bars[:upto], prices[:upto], kinds[:upto], flat_pct) if upto > 4 else None
            if older is not None:
                return {**older, "still_forming": True}
            return None
    pk, peaks, valleys = chosen
    return _as_trend(pk, peaks, valleys, bars, prices, upto)


def _as_trend(pk: str, peaks, valleys, bars, prices, upto: int) -> Dict:
    """The trend as the rest of the layer reads it, with its line.

    The line runs on the side price is working against: the peaks in a down trend, the valleys in
    an up one, and in a range the peaks (its ceiling is what a breakout has to clear)."""
    side = peaks if pk in (DOWN, FLAT) else valleys
    a, b = side[0], side[-1]
    days = max(bars[b] - bars[a], 1e-9)
    slope = (np.log(prices[b]) - np.log(prices[a])) / days
    return {"direction": pk, "role": "resistance" if pk == DOWN else "support" if pk == UP
            else ("resistance" if prices[peaks[-1]] >= prices[valleys[-1]] else "support"),
            "x1": float(bars[a]), "y1": float(np.log(prices[a])), "slope": float(slope),
            "first": float(bars[a]), "last": float(bars[b]),
            "points": [float(bars[a]), float(bars[b])],
            "peaks": [float(bars[i]) for i in peaks],
            "valleys": [float(bars[i]) for i in valleys],
            "peak_prices": [float(prices[i]) for i in peaks],
            "valley_prices": [float(prices[i]) for i in valleys],
            "touches": 2, "established_at": float(bars[upto]),
            "still_forming": upto < len(bars) - 1}


def range_now(bars: np.ndarray, prices: np.ndarray, kinds: np.ndarray, flat_pct: float,
              price_now: float) -> Optional[Dict]:
    """A range price is still inside IS the trend: "were in a 10% ranging pipe with more than 2
    peaks and valleys at the same height ... maybe its the previous trend if anything" (2026-10-06,
    at 2025-07-04, where the older up trend had been drawn instead).

    The last two peaks at one level, the last two valleys at one level, and price between that
    floor and that ceiling. Once price has left it, the range is not the answer any more and the
    trend is read past it - 2026-05-15 above the March range is "a downtrend clearly"."""
    if len(bars) < 4:
        return None
    upto = len(bars) - 1
    peaks, valleys = _pairs_at(bars, prices, kinds, upto, 2)
    if len(peaks) < 2 or len(valleys) < 2:
        return None
    if not (_all_level(prices, peaks, flat_pct) and _all_level(prices, valleys, flat_pct)):
        return None
    floor, ceiling = min(prices[i] for i in valleys), max(prices[i] for i in peaks)
    if not floor <= price_now <= ceiling:
        return None
    return {**_as_trend(FLAT, peaks, valleys, bars, prices, upto), "inside": True}


def at_bar(trend: Dict, bar: float) -> float:
    """What the trend line is worth at a bar."""
    return float(np.exp(trend["y1"] + trend["slope"] * (bar - trend["x1"])))

