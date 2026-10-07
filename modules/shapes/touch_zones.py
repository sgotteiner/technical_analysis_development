"""
A touch is a ZONE, not a dot (owner, 2026-10-05, drawn rather than written):

  "here is another example of a line and the boxes with touch zones. not touch dots like you do.
   touch zones. when you draw lines and explain to me based on what you drew them i expect to see
   things like"

His own two, measured off the strokes he saved: a flat line at ~30,800 across seven months of 2023,
with 2023-04-09 -> 04-21 (12 days, 2.85% tall) and 2023-06-19 -> 07-18 (29 days, 2.72% tall) drawn
on it. So a touch is a stretch of BARS that worked the level, and its box is as tall as the ground
those bars actually covered - not a mark on one high.

A zone ends when price leaves the band and stays away: `min_gap` bars outside it close the zone,
which is the visits rule (price has to leave and come back) with the band made explicit.
"""
from typing import Dict, List
import numpy as np


def touch_zones(price: float, band_pct: float, high: np.ndarray, low: np.ndarray, end: int,
                min_gap: int = 5, min_bars: int = 2, start: int = 0) -> List[Dict]:
    """Every stretch of bars up to `end` whose candle touched the band around `price`.

    A bar touches when its own low..high range reaches into the band - a wick counts, because a
    wick is how price tests a level.

    The zone's HEIGHT is the band, not the ground the bars covered: his own boxes are 2.85% and
    2.72% tall around a line price swung 12% through, and the candles stick out of them. What the
    bars reached is kept as `reach_top` / `reach_bottom` for the explanation, not for the shape.

    Each zone says whether it is a TOUCH or a BREAK: a touch arrives and leaves on the same side of
    the line, a break crosses it. That is what tells his two drawn zones from the third one the
    same search finds - April and June/July arrive from below and leave below; October arrives from
    below and leaves above, and he did not draw it. No threshold is involved.

    `min_bars` drops a single bar passing through on its way somewhere else - "there was a candle
    who broke the support in a tail but got back and i ignored this spike" (owner, 2026-10-05). It
    is a stated guess, not a searched one.
    """
    if price <= 0 or end < start:
        return []
    band = price * band_pct / 100
    lo, hi = price - band, price + band
    hits = np.flatnonzero((low[start:end + 1] <= hi) & (high[start:end + 1] >= lo)) + start
    if not len(hits):
        return []
    runs: List[List[int]] = [[int(hits[0])]]
    for b in hits[1:]:
        if b - runs[-1][-1] > min_gap:     # price left the band and stayed away: that visit ended
            runs.append([])
        runs[-1].append(int(b))
    return [_zone(r, high, low, price, lo, hi, end) for r in runs if len(r) >= min_bars]


def _side(high: np.ndarray, low: np.ndarray, lo: float, hi: float, frm: int, step: int,
          end: int) -> str:
    """Which side of the band price is on, at the first bar outside it in that direction."""
    i = frm
    while 0 <= i <= end:
        if low[i] > hi:
            return "above"
        if high[i] < lo:
            return "below"
        i += step
    return "open"          # it never left the band within the data


def _zone(run: List[int], high: np.ndarray, low: np.ndarray, price: float,
          lo: float, hi: float, end: int) -> Dict:
    a, b = run[0], run[-1]
    came = _side(high, low, lo, hi, a - 1, -1, end)
    left = _side(high, low, lo, hi, b + 1, +1, end)
    return {"from_bar": a, "to_bar": b, "bars": b - a + 1, "touching_bars": len(run),
            "top": float(hi), "bottom": float(lo),
            "height_pct": (hi / lo - 1) * 100 if lo > 0 else 0.0,
            "reach_top": float(np.max(high[a:b + 1])),      # what the bars actually covered,
            "reach_bottom": float(np.min(low[a:b + 1])),    # for the words, not for the box
            "came_from": came, "left_to": left,
            "kind": "touch" if came == left or "open" in (came, left) else "break",
            "price": float(price)}
