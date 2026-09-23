"""
S/R playground view — what the playground page draws for one "now" and one set of settings
(owner, 2026-09-22: change the settings and see the lines immediately; show more than 2 pairs,
or single lines). Per level: the ranked pipes, the ranked single lines and the swing legs the
width rules use. Only candles up to `end` are used (the shape blocks guarantee it).
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from modules.shapes.sr_settings import SRRules
from modules.shapes.sr_lines import candidate_lines, top_lines
from modules.shapes.point_lines import lines_from_points
from modules.shapes.recent_levels import recent_levels
from modules.shapes.trend_lines import trend_lines
from modules.shapes.sr_pipes import ranked_pipes, swing_legs, pipe_width
from modules.shapes.sr_turning_points import turning_points, PEAK

MAX_PAIRS = 50_000_000      # pipe-search budget per level; beyond it the view says "incomplete"


def _level_view(df, end, cfg, rules, pairs, singles, tp) -> Dict:
    m, period = cfg["magnitude"], cfg["period"]
    tp_cand, tp_full = tp(m * rules.candidate_ratio), tp(m)
    lines = candidate_lines(df, end, period, m, tp_cand, rules)
    info = {}
    pipes = ranked_pipes(df, end, period, m, pairs, tp_cand, tp_full, rules, MAX_PAIRS, info, lines) if pairs else []
    legs = swing_legs(df, end, period, m, tp_full)
    return {"pipes": [{"support": lo, "resistance": up, "width": pipe_width(lo, up)} for lo, up in pipes],
            "lines": top_lines(lines, singles) if singles else [],
            "candidates": len(lines), "complete": bool(info.get("complete", True)),
            "checked_down_to": info.get("checked_down_to"),
            "largest_swing": float(legs.max()) if len(legs) else None,
            "median_swing": float(np.median(legs)) if len(legs) else None}


MAX_POINTS_FOR_LINES = 400      # every pair against every point: beyond this it is too slow to watch


def swing_points(df: pd.DataFrame, end: int, size: float, cache: Optional[Dict] = None,
                 lookback: Optional[int] = None) -> list:
    """The peaks and valleys of a `size` zigzag confirmed by `end`, ready to draw."""
    cache = cache if cache is not None else {}
    tp = cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))
    known = tp["conf"] <= end
    if lookback:
        known &= tp["idx"] >= end - lookback + 1
    return [{"bar": int(i), "time": int(df.index[i].timestamp()), "price": float(np.exp(y)),
             "kind": "peak" if k == PEAK else "valley"}
            for i, k, y in zip(tp["idx"][known], tp["kind"][known], tp["y"][known])]


def point_lines(points: list, cfg, end: int) -> list:
    """Lines through the given swing points (modules/shapes/point_lines.py). A line must touch a
    point from the last `anchor_days` — the owner finds the recent S/R first, then its history."""
    x = np.array([p["bar"] for p in points], dtype=float)
    y = np.log(np.array([p["price"] for p in points], dtype=float)) if points else np.array([])
    anchor = end - cfg.anchor_days + 1 if cfg.anchor_days else None
    if cfg.mode == "touches":
        # every pair against every point; the owner's rule below only walks the recent points
        if len(points) > MAX_POINTS_FOR_LINES:
            raise ValueError(f"{len(points)} points is too many for the touch rule: raise the size or shorten the lookback")
        return {"lines": lines_from_points(x, y, cfg.tol_pct, cfg.min_touches, cfg.max_slope_pct, cfg.top, anchor)}
    kinds = np.array([1 if p["kind"] == "peak" else -1 for p in points], dtype=int)
    start = anchor if anchor is not None else 0
    return {"levels": recent_levels(x, y, start, cfg.tol_pct, cfg.max_history)[:cfg.top],
            "trends": trend_lines(x, y, kinds, start, cfg.tol_pct, cfg.min_touches)[:cfg.top]}


def playground_view(df: pd.DataFrame, end: int, levels: Dict, rules: SRRules, pairs: int = 1, singles: int = 0,
                    cache: Optional[Dict] = None) -> Dict:
    """`cache` may hold turning points of the WHOLE df per threshold; only points confirmed by
    `end` are ever used, so it is safe to share between calls with different `end`."""
    cache = cache if cache is not None else {}
    tp = lambda th: cache[th] if th in cache else cache.setdefault(th, turning_points(df, th))
    return {"end": int(end),
            "levels": {name: _level_view(df, end, cfg, rules, pairs, singles, tp) for name, cfg in levels.items()}}
