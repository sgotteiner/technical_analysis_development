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
from modules.shapes.level_clusters import merge_trends
from business_logic_services.level_rule import levels_from_points
from business_logic_services.move_lines import ladder_by_move, lines_by_move
from modules.shapes.swing_moves import leg_moves, running_move
from modules.shapes.swing_boxes import swing_boxes
from business_logic_services.setup_story import setup_story
from business_logic_services.precedents import picture_starts_at
from modules.shapes.price_zones import price_zones
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


TREND_SLOPE_PCT = 0.08      # %/day: how close two trends must be to count as one
MAX_POINTS_FOR_LINES = 400      # every pair against every point: beyond this it is too slow to watch
MIN_DOTS_FOR_A_LEVEL = 2        # one dot is a dot, not a level (owner, 2026-10-03)


def swing_points(df: pd.DataFrame, end: int, size: float, cache: Optional[Dict] = None,
                 lookback: Optional[int] = None) -> list:
    """The peaks and valleys of a `size` zigzag confirmed by `end`, ready to draw."""
    cache = cache if cache is not None else {}
    tp = cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))
    known = tp["conf"] <= end
    if lookback:
        known &= tp["idx"] >= end - lookback + 1
    # what each point is worth: the leg that ran into it, and the leg running now (owner, 2026-10-03)
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    moves = leg_moves(tp, high, low)
    now_move, _, _ = running_move(tp, high, low, end)
    return [{"bar": int(i), "time": int(df.index[i].timestamp()), "price": float(np.exp(y)),
             "kind": "peak" if k == PEAK else "valley", "move": float(m), "running_move": now_move}
            for i, k, y, m in zip(tp["idx"][known], tp["kind"][known], tp["y"][known], moves[known])]


def swing_box_view(df: pd.DataFrame, end: int, size: float, cache=None,
                   from_bar: float = 0.0) -> list:
    """Each peak and valley as the journey it is - support to resistance to support, and the
    opposite for a valley (owner, 2026-10-03: "i need to see what you do")."""
    cache = cache if cache is not None else {}
    tp = cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))
    boxes = swing_boxes(tp, df["High"].to_numpy(), df["Low"].to_numpy(), end, from_bar)
    t = df.index
    return [{**b, "from_time": int(t[b["from_bar"]].timestamp()),
             "to_time": int(t[b["to_bar"]].timestamp())} for b in boxes]


def picture_start(df: pd.DataFrame, end: int, size: float, band_pct: float, cache=None) -> float:
    """How far back the picture reaches: to the precedent of the level price is working now."""
    cache = cache if cache is not None else {}
    tp = cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx = tp["idx"][known]
    if len(idx) < 3:
        return 0.0
    bars = idx.astype(float)
    prices = np.where(tp["kind"][known] == PEAK, high[idx], low[idx]).astype(float)
    moves = leg_moves(tp, high, low)[known]
    now_move, _, _ = running_move(tp, high, low, end)
    close = df["Close"].to_numpy()
    return picture_starts_at(float(close[end]), now_move, bars, prices, moves, band_pct, end)


def story_view(df: pd.DataFrame, end: int, size: float, levels: list, trend: Optional[Dict],
               band_pct: float, cache=None) -> Dict:
    """The setup in words - explaining the lines the chart is ALREADY drawing, never finding its
    own (owner, 2026-10-03: the two must not be "completely different numbers")."""
    cache = cache if cache is not None else {}
    tp = cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx = tp["idx"][known]
    if len(idx) < 3 or not levels:
        return {}
    bars = idx.astype(float)
    prices = np.where(tp["kind"][known] == PEAK, high[idx], low[idx]).astype(float)
    moves = leg_moves(tp, high, low)[known]
    now_move, from_bar, _ = running_move(tp, high, low, end)
    t = df.index
    day = lambda b: t[int(b)].strftime("%Y-%m-%d")
    close = df["Close"].to_numpy()
    # every dot's box, so a line can show the journeys of the dots it is made of
    boxes_by_bar = {b["bar"]: {**b, "from_time": int(t[b["from_bar"]].timestamp()),
                               "to_time": int(t[b["to_bar"]].timestamp())}
                    for b in swing_boxes(tp, high, low, end)}
    story = setup_story(levels, trend, float(close[end]), float(close[max(0, end - 10)]),
                        now_move, from_bar, end, band_pct, day, bars, prices, moves, boxes_by_bar)
    for line in story["lines"]:
        line["times"] = [int(t[int(b)].timestamp()) for b in line["points"]]
        line["dates"] = [day(b) for b in line["points"]]
    return story


def _per_side(trends: list, per_side: int) -> list:
    """At most `per_side` trend lines for support and for resistance: the rest are variations."""
    kept = {"support": 0, "resistance": 0}
    out = []
    for t in trends:
        if kept[t["role"]] < per_side:
            kept[t["role"]] += 1
            out.append(t)
    return out


def point_lines(points: list, cfg, end: int, price_now: float = 0.0, price_before: float = 0.0,
                big_points: list = None, size: float = 0.0) -> list:
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
    band = cfg.merge_pct if cfg.merge_pct > 0 else cfg.tol_pct * 2
    if cfg.mode == "moves":
        # a touch is worth the move that ran into it, and a line matters when its moves are the
        # size of the move running now (owner, 2026-10-03). Kept beside the rule he already likes.
        moves = np.array([p.get("move", 0.0) for p in points], dtype=float)
        now_move = float(points[-1].get("running_move", 0.0)) if points else 0.0
        # "band width from the swing size, about half a swing" - his rule, so it is the default
        band = cfg.band_pct if cfg.band_pct else (size * 100 / 2 if size else band)
        lines = lines_by_move(x, y, kinds, moves, band, price_now, price_before, end,
                              current_move=now_move, age_scale=cfg.age_scale,
                              min_touches=max(2, cfg.min_visits - 1), top=cfg.top)
        return {"levels": lines, "trends": [], "current_move": now_move,
                "ladder": ladder_by_move(lines, price_now, cfg.targets_each_way or 3)}
    big = None
    if big_points:
        big = (np.array([p["bar"] for p in big_points], dtype=float),
               np.log(np.array([p["price"] for p in big_points], dtype=float)),
               np.array([1 if p["kind"] == "peak" else -1 for p in big_points], dtype=int))
    levels = levels_from_points(x, y, kinds, start, band, price_now, price_before, end,
                                min_visits=cfg.min_visits, targets_each_way=cfg.targets_each_way,
                                target_dots=big, target_band_pct=band * 2, top=cfg.top,
                                prefer=cfg.prefer)
    trends = trend_lines(x, y, kinds, start, cfg.tol_pct, cfg.min_touches)
    trends = merge_trends(trends, end, cfg.merge_pct, TREND_SLOPE_PCT)   # near-copies are one trend
    trends = _per_side(trends, cfg.trends_per_side)
    return {"levels": levels, "trends": trends}


def playground_view(df: pd.DataFrame, end: int, levels: Dict, rules: SRRules, pairs: int = 1, singles: int = 0,
                    cache: Optional[Dict] = None) -> Dict:
    """`cache` may hold turning points of the WHOLE df per threshold; only points confirmed by
    `end` are ever used, so it is safe to share between calls with different `end`."""
    cache = cache if cache is not None else {}
    tp = lambda th: cache[th] if th in cache else cache.setdefault(th, turning_points(df, th))
    return {"end": int(end),
            "levels": {name: _level_view(df, end, cfg, rules, pairs, singles, tp) for name, cfg in levels.items()}}
