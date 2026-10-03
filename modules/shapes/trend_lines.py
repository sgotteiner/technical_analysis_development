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

Every pair of same-kind points is still a candidate, and the answer is unchanged; the work per
pair is batched and pruned by the rules themselves. For one point i, all the lines i->j are
scored in one matrix instead of one at a time, and two exact filters come first:

  still touched now  -> the line must hit one of the points inside `anchor_from`, and there are
                        only a handful of those, so the pair is tested against them alone before
                        it is tested against the whole chart;
  enough touches     -> grouping touches into visits only ever drops bars, so a pair with fewer
                        RAW hits than `min_touches` can never pass.

At 7% on BTC daily that carries 8k of the 142k pairs into the per-line path.
"""
from typing import Dict, List
import numpy as np

PEAK = 1


def _visits(touched: List[float], min_gap: float) -> List[float]:
    """One visit per group of touches: price has to leave the line and come back (owner's rule for
    levels, applied to trends). Keeps the first bar of each group."""
    kept: List[float] = []
    for t in touched:
        if not kept or t - kept[-1] > min_gap:
            kept.append(t)
    return kept


def trend_lines(x: np.ndarray, y: np.ndarray, kind: np.ndarray, anchor_from: float, tol_pct: float,
                min_touches: int = 3, min_gap: float = 5) -> List[Dict]:
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    kind = np.asarray(kind, dtype=int)
    if len(x) < 2:
        return []
    tol = np.log(1 + tol_pct / 100)
    out: Dict = {}
    for role, want, side in (("resistance", PEAK, +1), ("support", -PEAK, -1)):
        sel = np.flatnonzero(kind == want)
        xs, ys = x[sel], y[sel]
        rec = np.flatnonzero(xs >= anchor_from)         # the points that make a trend "still on"
        if not len(rec):
            continue
        ys_rec = ys[rec]
        for i in range(len(xs)):
            dx = xs - xs[i]
            dx_rec = dx[rec]
            js = np.flatnonzero(dx[i + 1:] != 0) + i + 1       # every later point at another bar
            if not len(js):
                continue
            slopes = (ys[js] - ys[i]) / (xs[js] - xs[i])       # kept in j order: ties resolve as before
            slopes = slopes[side * slopes <= 0]   # rising resistance / falling support: not a trend
            if not len(slopes):
                continue
            still_on = (np.abs(ys_rec[None, :] - (ys[i] + slopes[:, None] * dx_rec[None, :])) <= tol).any(axis=1)
            slopes = slopes[still_on]
            if not len(slopes):
                continue
            dist = ys[None, :] - (ys[i] + slopes[:, None] * dx[None, :])
            hit = np.abs(dist) <= tol
            for r in np.flatnonzero(hit.sum(axis=1) >= min_touches):
                slope, row = float(slopes[r]), dist[r]
                touched = _visits(xs[hit[r]].tolist(), min_gap)  # neighbours are one visit, not two
                if len(touched) < min_touches:
                    continue
                first, last = min(touched), max(touched)
                if last < anchor_from:          # the trend is over: not part of today's picture
                    continue
                inside = (xs >= first) & (xs <= last)
                if (side * row[inside] > tol).any():      # price went through it before it ended
                    continue
                key = (len(touched), first, last, round(slope, 10))
                out.setdefault(key, {"x1": first, "y1": float(ys[i] + slope * (first - xs[i])),
                                     "slope": slope, "role": role, "touches": len(touched),
                                     "first": first, "last": last, "points": touched})
    return sorted(out.values(), key=lambda l: (l["touches"], l["last"] - l["first"], l["last"]), reverse=True)
