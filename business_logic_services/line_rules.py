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
from business_logic_services.setup_roster import keep_roster
from business_logic_services.trend_state import flat_for
from modules.shapes.level_clusters import merge_trends
from modules.shapes.point_lines import lines_from_points
from modules.shapes.trend_lines import trend_lines

TREND_SLOPE_PCT = 0.08          # %/day: how close two trends must be to count as one
MAX_POINTS_FOR_LINES = 400      # every pair against every dot: beyond this it is too slow to watch

# How wide a level may be, as a share of the MOVE RUNNING NOW. A constant cannot do this job and
# was measured failing at it: with a fixed 1.5% band the answer still held two lines 3.0% apart in
# a 12.7% move (2026-09-04) and 3.2% apart in a 14.1% move (2025-10-03) - "i dont care about 3%
# when the move is 10%" (owner, 2026-10-05). With the band taken from the move, the closest pair
# at those dates is 0.32x and 0.44x of it.
# Bounded by his own two dates, not picked: at 2025-10-03 his two supports are 1.6% apart and are
# ONE line, so the share is > 0.11; at 2026-09-04 the closest pair he approved is 7.1% apart and
# they are TWO, so it is < 0.56. This sits between, and is the first thing to search.
MOVE_BAND = 0.25


def _per_side(trends: list, per_side: int) -> list:
    """At most `per_side` trend lines for support and for resistance: the rest are variations."""
    kept = {"support": 0, "resistance": 0}
    out = []
    for t in trends:
        if kept[t["role"]] < per_side:
            kept[t["role"]] += 1
            out.append(t)
    return out


# A wrong-side filter used to live here: drop any support drawn above price and any resistance
# below it. It killed the rising "support" at 126,806 with price at 68,854 - but it also killed a
# BROKEN trend, which he wants kept: "it possible we already broke it and dont have 2 peaks and
# valleys yet so we didnt change the trend yet" (2026-10-05). The structure does the job better:
# setup_roster keeps the one line running the way the last two peaks and two valleys say, so a
# rising line in a down trend never gets chosen in the first place, broken or not.


def _arrays(points: list):
    x = np.array([p["bar"] for p in points], dtype=float)
    y = np.log(np.array([p["price"] for p in points], dtype=float)) if points else np.array([])
    kinds = np.array([1 if p["kind"] == "peak" else -1 for p in points], dtype=int)
    return x, y, kinds


def point_lines(points: list, cfg, end: int, price_now: float = 0.0, price_before: float = 0.0,
                big_points: list = None, size: float = 0.0, trend: Dict = None,
                turned_at: float = 0.0, yardstick: float = 0.0, move_from_bar: float = 0.0) -> Dict:
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
    # the band comes from the move unless he has set one by hand - the yardstick when given
    # (structure_scale: the move measured against the structure it is in), else the move running now
    now_move = yardstick or (float(points[-1].get("running_move", 0.0)) if points else 0.0)
    if not cfg.merge_pct and now_move > 0:
        band = now_move * MOVE_BAND
    big = _arrays(big_points) if big_points else None
    levels = levels_from_points(x, y, kinds, anchor if anchor is not None else 0, band,
                                price_now, price_before, end,
                                min_visits=cfg.min_visits, targets_each_way=cfg.targets_each_way,
                                target_dots=big, target_band_pct=band * 2, top=cfg.top,
                                prefer=cfg.prefer)
    trends = trend_lines(x, y, kinds, anchor if anchor is not None else 0, cfg.tol_pct, cfg.min_touches)
    trends = merge_trends(trends, end, cfg.merge_pct, TREND_SLOPE_PCT)   # near-copies are one trend
    trends = _per_side(trends, cfg.trends_per_side)
    # and then only what he asks to see: the level above, the level below, the one price is on,
    # and ONE trend - "i dont want no next and i want the last trend" (owner, 2026-10-05)
    levels, trends = keep_roster(levels, trends, x, np.exp(y), kinds, price_now, end,
                                 flat_for(now_move),      # "the same level" is a share of the move
                                 trend=trend,             # read at the move's scale, when given
                                 turned_at=turned_at, band_pct=band, move_pct=now_move,
                                 move_from_bar=move_from_bar, min_visits=cfg.min_visits)
    return {"levels": levels, "trends": trends}
