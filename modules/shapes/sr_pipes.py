"""
S/R pipes — each level's lower and upper line (modules/shapes/sr_lines.py) chosen TOGETHER.

Owner rules:
  (2026-09-21) two levels — higher (long period, big swings) and lower (short period, small
               swings) — each with a support (lower) and a resistance (upper) line: 4 lines.
  (2026-09-22) peaks / valleys by magnitude (10%; the higher level's 20% is Claude's default).
  (2026-09-22) not a widening shape, not too wide, not really narrow; a nice channel with a
               range inside or a triangle is what a pipe should be.
  (2026-09-22) the levels are found independently (no nesting).

The pipe is the (lower, upper) pair with the most significant touches in total such that
  together   both lines act at the same time: their touch periods overlap
  shape      upper slope <= lower slope (parallel or narrowing, never widening)
  width      median swing <= width <= largest swing, measured where both lines start (the widest
             point of a non-widening pipe); upper bound strict (owner), lower bound Claude's
  at now     at `end` the pipe is still open (lower below upper) and not wider than the largest
             swing — a triangle past its apex opens up the other way
Ties: the better lower line, then the better upper line. Exact over all pairs (vectorised).
  swing moves  legs of the `magnitude` zigzag inside the period, confirmed by `end`
"""
from typing import Dict, Optional, Tuple
import numpy as np
import pandas as pd
from modules.shapes.sr_lines import candidate_lines, line_key
from modules.shapes.sr_turning_points import turning_points

LEVELS = {"higher": {"period": 400, "magnitude": 0.20},
          "lower": {"period": 100, "magnitude": 0.10}}
MAX_DIVERGENCE = 0.0        # log/day; 0 = parallel or narrowing only


def swing_legs(df: pd.DataFrame, end: int, period: int, magnitude: float, tp: Optional[Dict] = None) -> np.ndarray:
    tp = tp if tp is not None else turning_points(df, magnitude)
    keep = (tp["conf"] <= end) & (tp["idx"] >= end - period + 1)
    return np.abs(np.diff(tp["y"][keep]))


def pipe_width(lower: Dict, upper: Dict) -> float:
    x0 = max(lower["x1"], upper["x1"])
    return (upper["y1"] + upper["slope"] * (x0 - upper["x1"])) - (lower["y1"] + lower["slope"] * (x0 - lower["x1"]))


def _ranks(lines):
    order = sorted(range(len(lines)), key=lambda i: line_key(lines[i]))
    rank = np.empty(len(lines), dtype=np.int64)
    rank[order] = np.arange(len(lines))
    return rank


def find_pipe(df: pd.DataFrame, end: int, period: int, magnitude: float, tp_half: Optional[Dict] = None,
              tp_full: Optional[Dict] = None) -> Tuple[Optional[Dict], Optional[Dict]]:
    lines = candidate_lines(df, end, period, magnitude, tp_half)
    legs = swing_legs(df, end, period, magnitude, tp_full)
    if len(lines) < 2 or not len(legs):
        return None, None
    lo_w, hi_w = float(np.median(legs)), float(legs.max())
    col = lambda k: np.array([l[k] for l in lines], dtype=float)
    s, x1, y1, t, last = (col(k) for k in ("slope", "x1", "y1", "touches", "last_touch"))
    at_end = y1 + s * (end - x1)
    x0 = np.maximum(x1[:, None], x1[None, :])                      # rows = lower line, cols = upper line
    width = (y1[None, :] + s[None, :] * (x0 - x1[None, :])) - (y1[:, None] + s[:, None] * (x0 - x1[:, None]))
    width_now = at_end[None, :] - at_end[:, None]
    ok = (x0 < np.minimum(last[:, None], last[None, :])) & (s[None, :] - s[:, None] <= MAX_DIVERGENCE) \
        & (width >= lo_w) & (width <= hi_w) & (width_now > 0) & (width_now <= hi_w)
    if not ok.any():
        return None, None
    n, rank = len(lines), _ranks(lines)
    score = (t[:, None] + t[None, :]).astype(np.int64) * n * n + rank[:, None] * n + rank[None, :]
    i, j = np.unravel_index(np.argmax(np.where(ok, score, -1)), score.shape)
    return lines[i], lines[j]


def sr_lines_at(df: pd.DataFrame, end: int, levels: Dict = LEVELS, cache: Optional[Dict] = None) -> Dict[str, Optional[Dict]]:
    """The 4 lines at bar `end`. `cache` may hold turning points computed once on the whole df
    ({threshold: turning_points(df, threshold)}); only points confirmed by `end` are used."""
    cache = cache if cache is not None else {}
    tp = lambda th: cache.setdefault(th, turning_points(df, th))
    out = {}
    for lvl, cfg in levels.items():
        m = cfg["magnitude"]
        out[f"{lvl}_support"], out[f"{lvl}_resistance"] = find_pipe(df, end, cfg["period"], m, tp(m / 2), tp(m))
    return out
