"""
Lines through swing points — the simplest rule there is (owner, 2026-09-23: "id like to see some
lines based on these points. they have settings too like maximum distance from the line").

The owner's method (2026-09-23): "found recent support and resistance and looked where else it was
in the history". So a line must touch a RECENT point (`anchor_from`, a bar index); the older
touches are what make it strong, not what makes it relevant.

  candidates  every line through two points (log price, any slope), at least one of them recent
  touch       a point within `tol_pct` of the line
  keep        lines with >= min_touches, and |slope| <= max_slope_pct when given
  rank        most touches, then the line that reaches furthest back, then the most recent touch
  collapse    lines with the same (touches, first, last) are near-copies: keep the first

No window and no magnitude rule: which points come in is the caller's choice (the size), and what
happens at a line (breakout, retest) is a later layer.
"""
from typing import Dict, List, Optional
import numpy as np


def line_price(line: Dict, x: float) -> float:
    return float(np.exp(line["y1"] + line["slope"] * (x - line["x1"])))


def lines_from_points(x: np.ndarray, y: np.ndarray, tol_pct: float, min_touches: int,
                      max_slope_pct: Optional[float] = None, top: Optional[int] = None,
                      anchor_from: Optional[float] = None) -> List[Dict]:
    """`x` bars, `y` log prices, both sorted by bar. Returns ranked lines."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if len(x) < 2:
        return []
    tol = np.log(1 + tol_pct / 100)
    a, b = np.triu_indices(len(x), k=1)
    apart = x[b] != x[a]                                   # one bar can hold a peak and a valley
    if anchor_from is not None:
        apart &= (x[b] >= anchor_from) | (x[a] >= anchor_from)      # at least one recent point
    a, b = a[apart], b[apart]
    if not len(a):
        return []
    slope = (y[b] - y[a]) / (x[b] - x[a])
    if max_slope_pct is not None:
        keep = np.abs(np.expm1(slope)) * 100 <= max_slope_pct
        a, b, slope = a[keep], b[keep], slope[keep]
        if not len(a):
            return []
    dist = y[None, :] - (y[a][:, None] + slope[:, None] * (x[None, :] - x[a][:, None]))
    hit = np.abs(dist) <= tol
    counts = hit.sum(axis=1)
    out = {}
    for r in np.flatnonzero(counts >= min_touches):
        touched = x[hit[r]]
        first, last = float(touched.min()), float(touched.max())
        key = (int(counts[r]), first, last)
        if key in out:
            continue
        out[key] = {"x1": first, "y1": float(y[a[r]] + slope[r] * (first - x[a[r]])), "slope": float(slope[r]),
                    "touches": int(counts[r]), "first": first, "last": last,
                    "points": [float(t) for t in touched]}
    ranked = sorted(out.values(), key=lambda l: (l["touches"], l["last"] - l["first"], l["last"]), reverse=True)
    return ranked[:top] if top else ranked
