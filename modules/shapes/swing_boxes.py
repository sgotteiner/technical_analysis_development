"""
A peak or a valley as a BOX, so the structure can be seen (owner, 2026-10-03):

  "peak is from support to resistance to support and valley is the opposite."

So a peak is not the single high - it is the whole journey: up from the support before it, to the
resistance, and back down to the support after it. The box is that journey:

  peak    left/right  the valleys either side        top  the peak's high
                                                     bottom  the lower of those two valleys
  valley  left/right  the peaks either side          bottom  the valley's low
                                                     top  the higher of those two peaks

Every box carries WHAT IT WAS DRAWN FROM, so the picture can show it rather than being a bare
rectangle (owner, 2026-10-05: "for everything you draw you have to explain based on what you drew
it... i wanna see the guidelines of those inside the boxes"):

  extreme      the high of a peak / the low of a valley - the line the box is hung on
  from_price   the anchor it came from, to_price the anchor it went to
  up_pct       the leg that ran into it, down_pct the leg away from it
  size_pct     the smaller of the two, which is what the point is worth as a turning point

And a box is not always one point: "boxes can be one or more peaks/valleys or a flat zone". Several
same-kind extremes at the same height are ONE box - his "same hight horizontal range" - carrying
the points it spans.

The last one is still happening: its far side has not formed yet, so the box runs to `end` and is
marked `open`. Nothing uses a point that is not confirmed by `end`, so there is no lookahead.
"""
from typing import Dict, List
import numpy as np

PEAK = 1


def swing_boxes(tp: Dict[str, np.ndarray], high: np.ndarray, low: np.ndarray, end: int,
                from_bar: float = 0.0) -> List[Dict]:
    """One box per confirmed turning point, in bar/price terms, ready to draw.

    `from_bar` bounds it to the picture, for the per-line journeys that belong to one answer. The
    layer that shows the structure itself passes 0: every dot on the chart has a box, or the eye
    cannot check the dots against the boxes at all.
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
        near, me = float(extreme[i - 1]), float(extreme[i])
        top, bottom = (me, min(near, far)) if is_peak else (max(near, far), me)
        up_pct = abs(me / near - 1) * 100
        down_pct = abs(far / me - 1) * 100
        out.append({
            "kind": "peak" if is_peak else "valley",
            "bar": here, "from_bar": left, "to_bar": right,
            "top": top, "bottom": bottom,
            "extreme": me, "from_price": near, "to_price": far,
            "height_pct": (top / bottom - 1) * 100 if bottom > 0 else 0.0,
            "bars": right - left,
            "up_pct": up_pct,            # the move that got there
            "down_pct": down_pct,        # and the move away from it
            "size_pct": min(up_pct, down_pct),   # what the point is worth as a turning point
            "points": [here],
            "open": open_ended,
        })
    return out


def flat_zones(boxes: List[Dict], tol_pct: float) -> List[Dict]:
    """Several same-kind extremes at the SAME HEIGHT, as one box (owner, 2026-10-05: "boxes can be
    one or more peaks/valleys or a flat zone"; 2026-10-04: "same hight horizontal range").

    Peaks are walked with peaks and valleys with valleys - the boxes alternate, so same-kind
    neighbours are never next to each other in the list. Each new one must sit within `tol_pct` of
    the run's first extreme. A zone of one is not a zone, so only runs of two or more are returned,
    and they are an ADDITION to the per-point boxes, never a replacement: the point boxes are what
    the eye checks the dots against.
    """
    out: List[Dict] = []

    for kind in ("peak", "valley"):
        run: List[Dict] = []
        for b in [x for x in boxes if x["kind"] == kind]:
            if run and abs(b["extreme"] / run[0]["extreme"] - 1) * 100 <= tol_pct:
                run.append(b)
                continue
            _flush(run, out)
            run = [b]
        _flush(run, out)
    return sorted(out, key=lambda z: z["from_bar"])


def _flush(run: List[Dict], out: List[Dict]) -> None:
    """One zone from a run of same-kind extremes, if there is more than one of them."""
    if len(run) < 2:
        return
    tops = [b["extreme"] for b in run]
    out.append({
            "kind": "flat " + run[0]["kind"] + "s",
        "bar": run[0]["bar"], "from_bar": run[0]["from_bar"], "to_bar": run[-1]["to_bar"],
        "top": max(b["top"] for b in run), "bottom": min(b["bottom"] for b in run),
        "extreme": float(np.mean(tops)),
        "from_price": run[0]["from_price"], "to_price": run[-1]["to_price"],
        "height_pct": (max(tops) / min(tops) - 1) * 100 if min(tops) > 0 else 0.0,
        "bars": run[-1]["to_bar"] - run[0]["from_bar"],
        "up_pct": run[0]["up_pct"], "down_pct": run[-1]["down_pct"],
        "size_pct": max(b["size_pct"] for b in run),
        "points": [b["bar"] for b in run],
        "spread_pct": (max(tops) / min(tops) - 1) * 100 if min(tops) > 0 else 0.0,
        "open": run[-1]["open"],
    })
