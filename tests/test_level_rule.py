"""
Tests for the level rule (business_logic_services/level_rule.py): clusters of dots, shown when
price is at them now or as the next ones up and down. The owner, 2026-09-24: "there are still some
really close lines that need to be merged" - whatever the line came from, the FINAL list may never
hold two lines closer than the band.
"""
import numpy as np
import pytest
from business_logic_services.level_rule import levels_from_points

PEAK, VALLEY = 1, -1


def _dots(pairs):
    return (np.array([p[0] for p in pairs], dtype=float),
            np.log(np.array([p[1] for p in pairs], dtype=float)),
            np.array([p[2] for p in pairs], dtype=int))


def _spread(levels):
    prices = sorted(l["price"] for l in levels)
    return min((b / a - 1) * 100 for a, b in zip(prices, prices[1:])) if len(prices) > 1 else 99


def test_no_two_lines_end_up_closer_than_the_band():
    x, y, k = _dots([(0, 60000, VALLEY), (10, 80000, PEAK), (20, 61500, VALLEY), (30, 81000, PEAK),
                     (40, 62500, VALLEY), (50, 82000, PEAK), (60, 60500, VALLEY), (70, 100000, PEAK),
                     (80, 99000, PEAK), (90, 61000, VALLEY)])
    levels = levels_from_points(x, y, k, start=50, band_pct=5.0, price_now=70000,
                                price_before=65000, end=90, targets_each_way=2)
    assert levels and _spread(levels) >= 5.0 - 1e-9, [round(l["price"]) for l in levels]


def test_a_target_that_repeats_a_recent_line_is_dropped():
    """80,108 (recent) and 80,600 (target) are one line."""
    x, y, k = _dots([(0, 80600, PEAK), (20, 60000, VALLEY), (40, 81500, PEAK), (60, 62000, VALLEY),
                     (80, 80100, PEAK), (90, 70000, VALLEY)])
    levels = levels_from_points(x, y, k, start=70, band_pct=5.0, price_now=79000,
                                price_before=75000, end=90, targets_each_way=2)
    near_80k = [l for l in levels if abs(l["price"] / 80500 - 1) < 0.05]
    assert len(near_80k) == 1 and not near_80k[0]["from_history"], "the recent line wins"


def test_a_target_far_from_everything_survives():
    x, y, k = _dots([(0, 106000, PEAK), (10, 60000, VALLEY), (20, 107000, PEAK), (30, 61000, VALLEY),
                     (80, 70000, PEAK), (85, 61000, VALLEY), (90, 70200, PEAK)])
    levels = levels_from_points(x, y, k, start=75, band_pct=5.0, price_now=68000,
                                price_before=64000, end=90, targets_each_way=2)
    assert any(abs(l["price"] / 106500 - 1) < 0.05 and l["from_history"] for l in levels), \
        [round(l["price"]) for l in levels]


def test_the_stronger_line_survives_a_clash():
    x, y, k = _dots([(0, 50000, VALLEY), (10, 70000, PEAK), (20, 50100, VALLEY), (30, 70100, PEAK),
                     (40, 50050, VALLEY), (50, 71500, PEAK), (60, 50200, VALLEY), (90, 51000, VALLEY)])
    levels = levels_from_points(x, y, k, start=55, band_pct=5.0, price_now=60000,
                                price_before=55000, end=90, targets_each_way=1)
    below = [l for l in levels if l["price"] < 60000]
    assert len(below) == 1 and below[0]["visits"] >= 4
