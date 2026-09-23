"""
Support / resistance lines — the owner's definition (2026-09-22):

    A line runs through (or close to) the MOST significant peaks and valleys over the period:
    it shows the trend. It may sit inside the graph and touch both peaks and valleys (split
    the graph), and a small overshoot does not move it — the overshooting point just is not a
    touch. Peaks and valleys are defined by magnitude, and a touch counts only if price moved
    at least `magnitude` away FROM THE LINE, so a rotated pipe counts the same as a flat one.

How a line is scored at bar `end` (only bars <= end are used, so it can be drawn live):
  points     turning points of a magnitude x candidate_ratio (1/2) zigzag (modules/shapes/sr_turning_points.py)
             confirmed by `end`, located inside the period
  candidates every line through two such points, in log price
  touch      a point within TOUCH_TOL of the line
  significant  a touch whose neighbouring turning points (before AND after, where confirmed
             by `end`) both lie >= magnitude away from the line on the other side: price came
             from X away and went back X away (Claude's reading: with one side only, a steep
             line gets a far neighbour for free)
  score      number of significant touches (>= rules.min_touches to be a line)
  best       most significant touches; ties -> most recent last touch, then earliest first
Every constant above is a setting in modules/shapes/sr_settings.py (defaults = the values here).
"""
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from modules.shapes.sr_turning_points import turning_points, PEAK
from modules.shapes.sr_settings import SRRules, DEFAULT_RULES

TOUCH_TOL = DEFAULT_RULES.tol          # "close to the line": within ~1.5%


def line_key(line: Dict) -> Tuple[int, int, int]:
    return line["touches"], line["last_touch"], -line["x1"]


def level_points(df: pd.DataFrame, end: int, period: int, magnitude: float, tp: Optional[Dict] = None,
                 rules: SRRules = DEFAULT_RULES):
    """Turning points confirmed by `end` (all of them, for neighbours) and those inside the period."""
    tp = tp if tp is not None else turning_points(df, magnitude * rules.candidate_ratio)
    known = tp["conf"] <= end
    pts = {k: v[known] for k, v in tp.items()}
    inside = pts["idx"] >= end - period + 1
    return pts, inside


def candidate_lines(df: pd.DataFrame, end: int, period: int, magnitude: float,
                    tp: Optional[Dict] = None, rules: SRRules = DEFAULT_RULES) -> List[Dict]:
    """Every line through two turning points of the period with >= min_touches significant touches."""
    pts, inside = level_points(df, end, period, magnitude, tp, rules)
    if inside.any():                    # only the period's points and the neighbour just before it matter
        keep = slice(max(int(np.argmax(inside)) - 1, 0), None)
        pts, inside = {k: v[keep] for k, v in pts.items()}, inside[keep]
    x, y, kind = pts["idx"].astype(float), pts["y"], pts["kind"]
    cand = np.flatnonzero(inside)
    if len(cand) < 2:
        return []
    need = np.log(1 + magnitude)
    a, b = np.triu_indices(len(cand), k=1)
    a, b = cand[a], cand[b]
    apart = x[b] != x[a]                     # a huge candle can be a valley AND a peak on one bar
    a, b = a[apart], b[apart]
    if not len(a):
        return []
    slope = (y[b] - y[a]) / (x[b] - x[a])
    line_at = lambda xs: y[a][:, None] + slope[:, None] * (xs[None, :] - x[a][:, None])
    dist = y[None, :] - line_at(x)                                   # every point vs every line
    # A neighbour's distance from the line, positive when it sits on its own side: a peak above
    # the line, a valley below. A touch's neighbours are of the other kind (points alternate).
    gap = np.where(kind == PEAK, 1.0, -1.0)[None, :] * dist
    # A neighbour not confirmed yet never decides: +inf when both sides must be far, -inf when one is enough.
    unknown = np.full((len(a), 1), np.inf if rules.both_sides else -np.inf)
    prev_gap = np.concatenate([unknown, gap[:, :-1]], axis=1)
    next_gap = np.concatenate([gap[:, 1:], unknown], axis=1)
    far = np.minimum(prev_gap, next_gap) if rules.both_sides else np.maximum(prev_gap, next_gap)
    sig = (np.abs(dist) <= rules.tol) & (far >= need) & inside[None, :]
    out = []
    for r in np.flatnonzero(sig.sum(axis=1) >= rules.min_touches):
        touched = pts["idx"][sig[r]]
        first = int(touched.min())
        out.append({"x1": first, "y1": float(y[a[r]] + slope[r] * (first - x[a[r]])), "slope": float(slope[r]),
                    "touches": int(len(touched)), "last_touch": int(touched.max()), "end": int(end)})
    return out


def best_line(df: pd.DataFrame, end: int, period: int, magnitude: float, tp: Optional[Dict] = None,
              rules: SRRules = DEFAULT_RULES) -> Optional[Dict]:
    cands = candidate_lines(df, end, period, magnitude, tp, rules)
    return max(cands, key=line_key) if cands else None


def ranked_lines(df: pd.DataFrame, end: int, period: int, magnitude: float, k: int, tp: Optional[Dict] = None,
                 rules: SRRules = DEFAULT_RULES) -> List[Dict]:
    return top_lines(candidate_lines(df, end, period, magnitude, tp, rules), k)


def top_lines(lines: List[Dict], k: int) -> List[Dict]:
    """The k best lines, one per line_key: lines with the same first touch, last touch and count
    are near-copies, so only the first found (the one best_line returns) is kept."""
    seen = {}
    for line in lines:
        seen.setdefault(line_key(line), line)
    return [seen[key] for key in sorted(seen, reverse=True)[:k]]
