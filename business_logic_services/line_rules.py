"""
Which dots make a line - the three rules the playground can be asked for, and nothing else.

The playground exists to COMPARE rules on his own chart, so three of them being reachable is the
point of the tool, not a leftover. What each rule is:

  owner    the rule he keeps: levels from the recent dots and their history, plus trend lines
  touches  the plain geometric one: any line through two dots, ranked by how many it touches
  moves    the same clusters, but a touch is worth the MOVE that ran into it

This module only picks the rule and feeds it: every rule lives in its own module, and the shape of
the answer is each rule's own.
"""
from typing import Dict
import numpy as np
from business_logic_services.level_rule import levels_from_points
from business_logic_services.move_lines import ladder_by_move, lines_by_move
from modules.shapes.level_clusters import merge_trends
from modules.shapes.point_lines import lines_from_points
from modules.shapes.trend_lines import trend_lines

TREND_SLOPE_PCT = 0.08          # %/day: how close two trends must be to count as one
MAX_POINTS_FOR_LINES = 400      # every pair against every dot: beyond this it is too slow to watch


def _per_side(trends: list, per_side: int) -> list:
    """At most `per_side` trend lines for support and for resistance: the rest are variations."""
    kept = {"support": 0, "resistance": 0}
    out = []
    for t in trends:
        if kept[t["role"]] < per_side:
            kept[t["role"]] += 1
            out.append(t)
    return out


def _arrays(points: list):
    x = np.array([p["bar"] for p in points], dtype=float)
    y = np.log(np.array([p["price"] for p in points], dtype=float)) if points else np.array([])
    kinds = np.array([1 if p["kind"] == "peak" else -1 for p in points], dtype=int)
    return x, y, kinds


def point_lines(points: list, cfg, end: int, price_now: float = 0.0, price_before: float = 0.0,
                big_points: list = None, size: float = 0.0) -> Dict:
    """Run the rule `cfg.mode` asks for over the given swing points."""
    x, y, kinds = _arrays(points)
    anchor = end - cfg.anchor_days + 1 if cfg.anchor_days else None
    band = cfg.merge_pct if cfg.merge_pct > 0 else cfg.tol_pct * 2
    if cfg.mode == "touches":
        # every pair against every point; the two rules below only walk the recent ones
        if len(points) > MAX_POINTS_FOR_LINES:
            raise ValueError(f"{len(points)} points is too many for the touch rule: raise the size or shorten the lookback")
        return {"lines": lines_from_points(x, y, cfg.tol_pct, cfg.min_touches, cfg.max_slope_pct, cfg.top, anchor)}
    if cfg.mode == "moves":
        # a touch is worth the move that ran into it, and a line matters when its moves are the
        # size of the move running now (owner, 2026-10-03). Kept beside the rule he already likes.
        moves = np.array([p.get("move", 0.0) for p in points], dtype=float)
        now_move = float(points[-1].get("running_move", 0.0)) if points else 0.0
        # "band width from the swing size, about half a swing" - his rule, so it is the default
        band = cfg.band_pct if cfg.band_pct else (size * 100 / 2 if size else band)
        lines = lines_by_move(x, y, kinds, moves, band, price_now, price_before, end,
                              current_move=now_move,
                              min_touches=max(2, cfg.min_visits - 1), top=cfg.top)
        return {"levels": lines, "trends": [], "current_move": now_move,
                "ladder": ladder_by_move(lines, price_now, cfg.targets_each_way or 3)}
    big = _arrays(big_points) if big_points else None
    levels = levels_from_points(x, y, kinds, anchor if anchor is not None else 0, band,
                                price_now, price_before, end,
                                min_visits=cfg.min_visits, targets_each_way=cfg.targets_each_way,
                                target_dots=big, target_band_pct=band * 2, top=cfg.top,
                                prefer=cfg.prefer)
    trends = trend_lines(x, y, kinds, anchor if anchor is not None else 0, cfg.tol_pct, cfg.min_touches)
    trends = merge_trends(trends, end, cfg.merge_pct, TREND_SLOPE_PCT)   # near-copies are one trend
    return {"levels": levels, "trends": _per_side(trends, cfg.trends_per_side)}
