"""
Tests for trend lines (modules/shapes/trend_lines.py), the owner's rules (2026-09-23/24):
  - "for diagonal lines its the recent trend not history": the line must still be touched now,
    but it may start as far back as the trend goes (his own line ran Sep 2025 -> Aug 2026, and a
    120-day window was "not long enough");
  - "i dont think up trends support (above the graph) or down trends below are helpful": a falling
    line is resistance and lives on the peaks; a rising line is support and lives on the valleys.
    Nothing may poke past the line between its first and last touch.
"""
import numpy as np
import pytest
from modules.shapes.trend_lines import trend_lines

PEAK, VALLEY = 1, -1


def _pts(pairs):
    x = np.array([p[0] for p in pairs], dtype=float)
    y = np.log(np.array([p[1] for p in pairs], dtype=float))
    kind = np.array([p[2] for p in pairs], dtype=int)
    return x, y, kind


def _falling_peaks():
    # peaks 100 -> 80 over 200 bars, valleys well below, one recent peak at bar 190
    return _pts([(0, 100, PEAK), (20, 70, VALLEY), (60, 94, PEAK), (90, 65, VALLEY),
                 (120, 88, PEAK), (150, 60, VALLEY), (190, 81, PEAK), (195, 62, VALLEY)])


def test_a_falling_resistance_through_peaks_is_found_however_far_back_it_starts():
    x, y, kind = _falling_peaks()
    lines = trend_lines(x, y, kind, anchor_from=170, tol_pct=1.5, min_touches=3)
    assert lines, "the falling line through the peaks must be found"
    best = lines[0]
    assert best["role"] == "resistance" and best["slope"] < 0
    assert best["first"] == 0 and best["last"] == 190 and best["touches"] == 4


def test_a_rising_support_comes_from_the_valleys():
    x, y, kind = _pts([(0, 60, VALLEY), (30, 90, PEAK), (60, 66, VALLEY), (90, 95, PEAK),
                       (120, 72, VALLEY), (180, 78, VALLEY), (185, 100, PEAK)])
    lines = trend_lines(x, y, kind, anchor_from=170, tol_pct=2.0, min_touches=3)
    assert lines and lines[0]["role"] == "support" and lines[0]["slope"] > 0


def test_a_rising_line_through_peaks_is_not_a_trend_line():
    """An "up trend resistance above the graph" is noise (owner)."""
    x, y, kind = _pts([(0, 80, PEAK), (20, 60, VALLEY), (60, 90, PEAK), (90, 65, VALLEY), (190, 100, PEAK)])
    assert trend_lines(x, y, kind, anchor_from=170, tol_pct=1.5, min_touches=3) == []


def test_a_line_that_price_pokes_through_before_its_last_touch_is_dropped():
    x, y, kind = _falling_peaks()
    x = np.append(x, 130.0); y = np.append(y, np.log(120)); kind = np.append(kind, PEAK)
    order = np.argsort(x)
    lines = trend_lines(x[order], y[order], kind[order], anchor_from=170, tol_pct=1.5, min_touches=3)
    assert all(l["first"] > 130 or l["last"] < 130 for l in lines)


def test_a_trend_line_must_still_be_touched_now():
    x, y, kind = _falling_peaks()                       # last peak at 190
    assert trend_lines(x, y, kind, anchor_from=193, tol_pct=1.5, min_touches=3) == []


def test_min_touches_and_ranking():
    x, y, kind = _falling_peaks()
    assert trend_lines(x, y, kind, anchor_from=170, tol_pct=1.5, min_touches=5) == []
    lines = trend_lines(x, y, kind, anchor_from=170, tol_pct=1.5, min_touches=2)
    assert [l["touches"] for l in lines] == sorted([l["touches"] for l in lines], reverse=True)


def test_touches_on_neighbouring_bars_count_once():
    """The owner's rule for levels applies to trends: price must leave and come back.
    A line "touched" on 2026-06-05 and 06-06 was touched once, not twice."""
    x, y, kind = _pts([(0, 100, PEAK), (20, 70, VALLEY), (100, 88, PEAK), (101, 87.9, PEAK),
                       (150, 60, VALLEY), (190, 81, PEAK)])
    lines = trend_lines(x, y, kind, anchor_from=170, tol_pct=1.5, min_touches=3)
    for l in lines:
        gaps = [b - a for a, b in zip(l["points"], l["points"][1:])]
        assert all(g > 5 for g in gaps), l["points"]


def test_empty_input():
    empty = np.array([])
    assert trend_lines(empty, empty, empty.astype(int), 0, 1.5, 2) == []
