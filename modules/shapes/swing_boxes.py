"""
A peak or a valley as a BOX, so the structure can be seen (owner, 2026-10-03):

  "peak is from support to resistance to support and valley is the opposite."

So a peak is not the single high - it is the whole journey: up from the support before it, to the
resistance, and back down to the support after it. The box is that journey:

  peak    left/right  the valleys either side        top  the peak's high
                                                     bottom  the lower of those two valleys
  valley  left/right  the peaks either side          bottom  the valley's low
                                                     top  the higher of those two peaks

The last one is still happening: its far side has not formed yet, so the box runs to `end` and is
marked `open`. Nothing uses a point that is not confirmed by `end`, so there is no lookahead.
"""
from typing import Dict, List
import numpy as np

PEAK = 1


def swing_boxes(tp: Dict[str, np.ndarray], high: np.ndarray, low: np.ndarray, end: int,
                from_bar: float = 0.0) -> List[Dict]:
    """One box per confirmed turning point, in bar/price terms, ready to draw.

    `from_bar` bounds it to the picture. There is no reason to draw the structure of 2018 when
    the picture reaches back to the precedent and no further (owner, 2026-10-03: "why up to
    2018?") - and 722 boxes buried his own drawings under 1,066 nodes.
    """
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx, kind = tp["idx"][known], tp["kind"][known]
    if len(idx) < 2:
        return []
    extreme = np.where(kind == PEAK, high[idx], low[idx]).astype(float)
    out: List[Dict] = []
    for i in range(len(idx)):
        if i == 0 or idx[i] < from_bar:
            continue                       # nothing before it: the journey has no start to show
        left, here = int(idx[i - 1]), int(idx[i])
        is_peak = kind[i] == PEAK
        if i + 1 < len(idx):
            right, far = int(idx[i + 1]), float(extreme[i + 1])
            open_ended = False
        else:                              # still forming: it runs to now
            right = int(end)
            far = float(np.min(low[here:end + 1]) if is_peak else np.max(high[here:end + 1]))
            open_ended = True
        near = float(extreme[i - 1])
        if is_peak:
            top, bottom = float(extreme[i]), min(near, far)     # support -> resistance -> support
        else:
            bottom, top = float(extreme[i]), max(near, far)     # resistance -> support -> resistance
        out.append({
            "kind": "peak" if is_peak else "valley",
            "bar": here, "from_bar": left, "to_bar": right,
            "top": top, "bottom": bottom,
            "height_pct": (top / bottom - 1) * 100 if bottom > 0 else 0.0,
            "bars": right - left,
            "up_pct": abs(float(extreme[i]) / near - 1) * 100,    # the move that got there
            "down_pct": abs(far / float(extreme[i]) - 1) * 100,   # and the move away from it
            "open": open_ended,
        })
    return out
