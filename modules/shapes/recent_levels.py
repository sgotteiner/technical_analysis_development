"""
The owner's way of finding lines (2026-09-23):

  "i didnt count lines i looked for the previous peak/valley of similar magnitude (similar shape)…
   it happend to be there the last time we saw such a shape at that price. thats for horizontal
   lines. for diagonal lines its the recent trend not history."

So:
  recent_levels       every RECENT swing point gives a horizontal level at its own price; history
                      only says how often that price acted before. Recent points within `tol` of
                      each other are one level. Ranked by history touches, then by the most recent.
  recent_trend_lines  lines through recent points only - the trend of the current move, never a
                      search through history.

`anchor_from` is the bar where "recent" starts. Touch = within `tol_pct` of the price / line.
"""
from typing import Dict, List, Optional
import numpy as np


def recent_levels(x: np.ndarray, y: np.ndarray, anchor_from: float, tol_pct: float,
                  max_history: Optional[int] = None) -> List[Dict]:
    """`max_history` keeps only the level's most recent visits before `anchor_from` (owner,
    2026-09-24: "i can see it in the history twice before the current maybe one is enough")."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    if not len(x):
        return []
    tol = np.log(1 + tol_pct / 100)
    recent = np.flatnonzero(x >= anchor_from)
    levels: List[Dict] = []
    for i in recent[::-1]:                       # newest first, so a level keeps its latest price
        if any(abs(y[i] - lv["y"]) <= tol for lv in levels):
            continue                             # the same level, touched again a few bars later
        near = np.abs(y - y[i]) <= tol
        touched = x[near]
        if max_history is not None:
            old = touched[touched < anchor_from]
            if len(old) > max_history:
                touched = touched[touched >= old[-max_history] if max_history else touched >= anchor_from]
        levels.append({"y": float(y[i]), "price": float(np.exp(y[i])), "anchor": float(x[i]),
                       "touches": int(len(touched)), "history": int((touched < anchor_from).sum()),
                       "first": float(touched.min()), "last": float(touched.max()),
                       "points": [float(t) for t in touched]})
    levels.sort(key=lambda lv: (lv["history"], lv["anchor"]), reverse=True)
    return levels


def recent_trend_lines(x: np.ndarray, y: np.ndarray, anchor_from: float, tol_pct: float,
                       min_touches: int = 2) -> List[Dict]:
    """Lines through the recent points only: the trend of the move we are in."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    keep = np.flatnonzero((x >= anchor_from) if len(x) else [])
    if len(keep) < 2:
        return []
    xs, ys = x[keep], y[keep]
    tol = np.log(1 + tol_pct / 100)
    out: Dict = {}
    for i in range(len(xs)):
        for j in range(i + 1, len(xs)):
            if xs[j] == xs[i]:
                continue
            slope = (ys[j] - ys[i]) / (xs[j] - xs[i])
            hit = np.abs(ys - (ys[i] + slope * (xs - xs[i]))) <= tol
            if hit.sum() < min_touches:
                continue
            touched = xs[hit]
            key = (int(hit.sum()), float(touched.min()), float(touched.max()))
            out.setdefault(key, {"x1": float(touched.min()), "slope": float(slope),
                                 "y1": float(ys[i] + slope * (touched.min() - xs[i])),
                                 "touches": int(hit.sum()), "first": float(touched.min()),
                                 "last": float(touched.max()), "points": [float(t) for t in touched]})
    return sorted(out.values(), key=lambda l: (l["touches"], l["last"] - l["first"], l["last"]), reverse=True)
