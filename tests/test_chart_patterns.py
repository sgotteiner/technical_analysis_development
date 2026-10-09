"""
The chart patterns (modules/patterns/chart_patterns.py) on made-up peaks and valleys, decided on the
first close through the neckline. "The same level" is 3% here.
"""
import numpy as np
from modules.patterns.chart_patterns import cup_handle, double, head_shoulders

SAME = 3.0


def test_double_top_is_decided_on_the_first_close_under_the_valley():
    pts = [(1, 100.0, 1), (3, 90.0, -1), (5, 101.0, 1)]
    close = np.array([95, 100, 95, 90, 95, 100, 93, 89, 88], dtype=float)
    p = double(pts, close, 7, SAME, top=True)
    assert p["type"] == "double_top" and p["target"] == 90.0 - 11.0
    assert double(pts, close, 8, SAME, top=True) is None          # only the first close under it


def test_two_peaks_at_different_levels_are_no_double_top():
    pts = [(1, 100.0, 1), (3, 90.0, -1), (5, 110.0, 1)]
    close = np.array([95, 100, 95, 90, 95, 110, 93, 89], dtype=float)
    assert double(pts, close, 7, SAME, top=True) is None


def test_head_and_shoulders():
    pts = [(1, 100.0, 1), (2, 90.0, -1), (3, 115.0, 1), (4, 90.0, -1), (5, 101.0, 1)]
    close = np.array([95, 100, 90, 115, 90, 101, 95, 89], dtype=float)
    p = head_shoulders(pts, close, 7, SAME, top=True)
    assert p["direction"] == "down" and p["target"] == 90.0 - 25.0


def test_cup_and_handle_needs_the_handle_in_the_upper_half():
    pts = [(1, 100.0, 1), (5, 70.0, -1), (9, 100.0, 1)]
    close = np.array([90, 100, 95, 85, 75, 70, 75, 85, 95, 100, 92, 96, 101], dtype=float)
    low = close - 1
    assert cup_handle(pts, close, low, 12, SAME)["target"] == 130.0
    deep = low.copy(); deep[10] = 80.0                            # the handle fell past the middle
    assert cup_handle(pts, close, deep, 12, SAME) is None
