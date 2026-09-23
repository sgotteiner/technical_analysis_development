"""
Tests for the owner's actual method (modules/shapes/recent_levels.py), stated 2026-09-23:
"found recent support and resistance and looked where else it was in the history" and, for
diagonals, "its the recent trend not history".

  levels       one per RECENT swing point: its price is the level; history only adds touches
               (where that price acted before) and never picks the level
  trend lines  drawn through recent points only, never through history
"""
import numpy as np
import pytest
from modules.shapes.recent_levels import recent_levels, recent_trend_lines


def _pts(pairs):
    x = np.array([p[0] for p in pairs], dtype=float)
    y = np.log(np.array([p[1] for p in pairs], dtype=float))
    return x, y


def test_a_level_comes_from_a_recent_point_and_history_only_counts_touches():
    # price acted at 100 long ago (bars 0, 20) and is at 100 again now (bar 100)
    x, y = _pts([(0, 100), (10, 70), (20, 100.5), (30, 60), (90, 65), (100, 99.6)])
    levels = recent_levels(x, y, anchor_from=80, tol_pct=1.5)
    assert len(levels) == 2                                     # the two recent points: 65 and ~100
    top = levels[0]
    assert top["price"] == pytest.approx(99.6, rel=0.001)       # the level IS the recent point's price
    assert top["touches"] == 3 and top["history"] == 2          # two older visits
    assert top["first"] == 0 and top["last"] == 100


def test_levels_are_ranked_by_how_often_that_price_acted_before():
    x, y = _pts([(0, 100), (10, 70), (20, 100), (30, 60), (40, 100), (50, 55), (60, 80), (95, 80.3), (100, 99.8)])
    levels = recent_levels(x, y, anchor_from=90, tol_pct=1.5)
    assert [round(l["price"]) for l in levels] == [100, 80]
    assert levels[0]["history"] == 3 and levels[1]["history"] == 1


def test_a_recent_point_with_no_history_is_still_a_level_but_last():
    x, y = _pts([(0, 100), (10, 70), (20, 100), (95, 42), (100, 99.5)])
    levels = recent_levels(x, y, anchor_from=90, tol_pct=1.5)
    assert [l["price"] for l in levels] == pytest.approx([99.5, 42], rel=1e-6)
    assert levels[-1]["history"] == 0 and levels[-1]["touches"] == 1


def test_nearby_recent_points_do_not_make_two_copies_of_the_same_level():
    x, y = _pts([(0, 100), (10, 70), (20, 100), (94, 99.4), (97, 60), (100, 100.3)])
    levels = recent_levels(x, y, anchor_from=90, tol_pct=1.5)
    assert [round(l["price"]) for l in levels] == [100, 60]      # 99.4 and 100.3 are one level


def test_history_can_be_cut_to_the_last_visits():
    """The owner, 2026-09-24: "i can see it in the history twice before the current maybe one is
    enough" - the level keeps only its most recent visits, not everything back to 2021."""
    x, y = _pts([(0, 100), (5, 70), (10, 100), (15, 70), (20, 100), (25, 70), (95, 65), (100, 100)])
    all_history = recent_levels(x, y, anchor_from=90, tol_pct=1.5)[0]
    assert all_history["history"] == 3 and all_history["first"] == 0
    one = recent_levels(x, y, anchor_from=90, tol_pct=1.5, max_history=1)[0]
    assert one["history"] == 1 and one["first"] == 20 and one["touches"] == 2
    two = recent_levels(x, y, anchor_from=90, tol_pct=1.5, max_history=2)[0]
    assert two["history"] == 2 and two["first"] == 10


def test_trend_lines_use_recent_points_only():
    # an old rising line (bars 0..40) and a recent falling one (bars 90..100)
    x, y = _pts([(0, 50), (10, 40), (20, 60), (30, 45), (40, 70), (90, 100), (95, 80), (100, 90), (105, 70)])
    lines = recent_trend_lines(x, y, anchor_from=85, tol_pct=2.0, min_touches=2)
    assert lines and all(l["first"] >= 85 for l in lines)
    assert all(l["last"] <= 105 for l in lines)


def test_trend_lines_need_two_recent_points():
    x, y = _pts([(0, 50), (10, 40), (20, 60), (100, 90)])
    assert recent_trend_lines(x, y, anchor_from=90, tol_pct=2.0, min_touches=2) == []


def test_empty_input():
    empty = np.array([])
    assert recent_levels(empty, empty, 0, 1.5) == []
    assert recent_trend_lines(empty, empty, 0, 1.5, 2) == []
