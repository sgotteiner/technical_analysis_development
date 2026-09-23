"""
Tests for lines drawn through swing points (modules/shapes/point_lines.py).
The owner, 2026-09-23: "id like to see some lines based on these points. they have settings too
like maximum distance from the line and stuff like that."
The simplest possible rule: a line through two points; every point within `tol` of it is a touch;
keep the lines with at least `min_touches`. No window, no magnitude rule - those are separate
layers. Lines are ranked by touches, then by the most recent touch, then by the earliest start.
"""
import numpy as np
import pytest
from modules.shapes.point_lines import lines_from_points, line_price


def _pts(pairs):
    x = np.array([p[0] for p in pairs], dtype=float)
    y = np.log(np.array([p[1] for p in pairs], dtype=float))
    return x, y


def test_horizontal_line_through_three_points():
    x, y = _pts([(0, 100), (10, 80), (20, 100.5), (30, 75), (40, 99.5)])
    lines = lines_from_points(x, y, tol_pct=1.5, min_touches=3)
    assert lines, "the 100 level must be found"
    best = lines[0]
    assert best["touches"] == 3 and best["first"] == 0 and best["last"] == 40
    assert line_price(best, 20) == pytest.approx(100, rel=0.01)


def test_tolerance_decides_what_counts_as_a_touch():
    x, y = _pts([(0, 100), (10, 80), (20, 103), (30, 75), (40, 100)])
    tight = lines_from_points(x, y, tol_pct=1.5, min_touches=3)
    loose = lines_from_points(x, y, tol_pct=4.0, min_touches=3)
    assert not tight and loose and loose[0]["touches"] == 3


def test_min_touches_filters():
    x, y = _pts([(0, 100), (10, 80), (20, 100), (30, 60)])
    assert lines_from_points(x, y, 1.5, min_touches=2)
    assert not lines_from_points(x, y, 1.5, min_touches=3)


def test_a_diagonal_is_found_and_slope_can_be_limited():
    x, y = _pts([(0, 100), (10, 80), (20, 110), (30, 85), (40, 121)])       # peaks rising ~1%/bar
    diag = [l for l in lines_from_points(x, y, 1.5, 3) if l["slope"] > 0]
    assert diag and diag[0]["touches"] == 3
    flat_only = lines_from_points(x, y, 1.5, 3, max_slope_pct=0.1)
    assert all(abs(np.expm1(l["slope"]) * 100) <= 0.1 for l in flat_only)


def test_near_duplicate_lines_are_collapsed():
    x, y = _pts([(0, 100), (10, 80), (20, 100.3), (30, 75), (40, 99.8), (50, 70)])
    lines = lines_from_points(x, y, 1.5, 3)
    keys = [(l["touches"], l["first"], l["last"]) for l in lines]
    assert len(keys) == len(set(keys))


def test_ranked_by_touches_then_recency():
    x, y = _pts([(0, 50), (5, 40), (10, 50), (15, 30), (20, 100), (25, 80), (30, 100), (35, 70), (40, 100)])
    lines = lines_from_points(x, y, 1.5, 2)
    assert lines[0]["touches"] == 3 and line_price(lines[0], 40) == pytest.approx(100, rel=0.01)
    assert [l["touches"] for l in lines] == sorted([l["touches"] for l in lines], reverse=True)


def test_top_k_and_empty_input():
    x, y = _pts([(0, 100), (10, 80), (20, 100), (30, 75), (40, 100), (50, 60), (60, 79)])
    assert len(lines_from_points(x, y, 1.5, 2, top=3)) == 3
    assert lines_from_points(np.array([]), np.array([]), 1.5, 2) == []


def test_a_line_must_touch_a_recent_point():
    """The owner's method (2026-09-23): find the recent support / resistance, THEN look back for
    where that level acted before. A line made only of old points is not part of today's setup."""
    # an old level at 100 (bars 0, 20, 40) and a level at 60 that is still being touched (30, 90, 100)
    x, y = _pts([(0, 100), (10, 80), (20, 100), (30, 60), (40, 100), (50, 80), (90, 60), (100, 60.3)])
    anchored = lines_from_points(x, y, 1.5, 3, anchor_from=80)
    assert anchored and all(max(l["points"]) >= 80 for l in anchored)
    old_only = [l for l in lines_from_points(x, y, 1.5, 3) if max(l["points"]) < 80]
    assert old_only and not [l for l in anchored if max(l["points"]) < 80]


def test_history_touches_still_count_behind_the_anchor():
    """The recent point anchors the line; the older touches are what make it strong."""
    x, y = _pts([(0, 100), (10, 80), (20, 100), (30, 70), (40, 100), (95, 60), (100, 99.5)])
    best = lines_from_points(x, y, 1.5, 3, anchor_from=90)[0]
    assert best["touches"] == 4 and best["first"] == 0 and best["last"] == 100


def test_ranked_by_touches_then_by_how_far_back_the_line_reaches():
    x, y = _pts([(0, 100), (10, 80), (20, 100), (50, 70), (60, 50), (70, 50.2), (95, 60), (100, 100), (105, 50)])
    ranked = lines_from_points(x, y, 1.5, 3, anchor_from=90)
    spans = [l["last"] - l["first"] for l in ranked]
    touches = [l["touches"] for l in ranked]
    assert touches == sorted(touches, reverse=True)
    assert spans[0] >= spans[-1]


def test_two_points_on_the_same_bar_never_make_a_line():
    x, y = _pts([(0, 100), (10, 80), (10, 90), (20, 100)])
    for l in lines_from_points(x, y, 1.5, 2):
        assert np.isfinite(l["slope"])
