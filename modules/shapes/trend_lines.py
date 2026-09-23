"""
Trend lines — the owner's rules (2026-09-23/24):

  "for diagonal lines its the recent trend not history"   -> the line must still be touched now
                                                             (a touch at or after `anchor_from`)
  "it didnt go long enough"                               -> but it may START as far back as the
                                                             trend goes: no window on the past
  "i dont think up trends support (above the graph) or    -> a falling line is RESISTANCE and runs
   down trends below are helpful"                            on peaks; a rising line is SUPPORT and
                                                             runs on valleys; nothing else
  a line that price has already gone through              -> dropped: between its first and last
                                                             touch no point of its own kind may sit
                                                             more than `tol` on the far side

Ranked by touches, then by how far the line reaches, then by the most recent touch.
"""
from typing import Dict, List
import numpy as np

PEAK = 1


def trend_lines(x: np.ndarray, y: np.ndarray, kind: np.ndarray, anchor_from: float, tol_pct: float,
                min_touches: int = 3) -> List[Dict]:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    kind = np.asarray(kind, dtype=int)
    if len(x) < 2:
        return []
    tol = np.log(1 + tol_pct / 100)
    out: Dict = {}
    for role, want, side in (("resistance", PEAK, +1), ("support", -PEAK, -1)):
        sel = np.flatnonzero(kind == want)
        xs, ys = x[sel], y[sel]
        for i in range(len(xs)):
            for j in range(i + 1, len(xs)):
                if xs[j] == xs[i]:
                    continue
                slope = (ys[j] - ys[i]) / (xs[j] - xs[i])
                if side * slope > 0:            # rising resistance / falling support: not a trend line
                    continue
                dist = ys - (ys[i] + slope * (xs - xs[i]))
                hit = np.abs(dist) <= tol
                if hit.sum() < min_touches:
                    continue
                touched = xs[hit]
                first, last = float(touched.min()), float(touched.max())
                if last < anchor_from:          # the trend is over: not part of today's picture
                    continue
                inside = (xs >= first) & (xs <= last)
                if (side * dist[inside] > tol).any():      # price went through it before it ended
                    continue
                key = (int(hit.sum()), first, last, round(float(slope), 10))
                out.setdefault(key, {"x1": first, "y1": float(ys[i] + slope * (first - xs[i])),
                                     "slope": float(slope), "role": role, "touches": int(hit.sum()),
                                     "first": first, "last": last, "points": [float(t) for t in touched]})
    return sorted(out.values(), key=lambda l: (l["touches"], l["last"] - l["first"], l["last"]), reverse=True)
