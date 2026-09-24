"""
Tests for merging near-copy trend lines (modules/shapes/level_clusters.merge_trends).
The owner, 2026-09-24: "there are 3 trend lines again" - three lines along the same trend are one
line. Two trends merge when they run on the same side, hold nearly the same price at "now" and
have nearly the same slope; the one with more touches and the longer reach survives.
"""
import numpy as np
import pytest
from modules.shapes.level_clusters import merge_trends


def _trend(slope_pct_day, at_now, touches=3, first=0, last=100, role="resistance"):
    slope = np.log1p(slope_pct_day / 100)
    return {"role": role, "slope": slope, "touches": touches, "first": first, "last": last,
            "x1": first, "y1": float(np.log(at_now) - slope * (last - first)), "points": [first, last]}


def _at_now(t, now=100):
    return float(np.exp(t["y1"] + t["slope"] * (now - t["x1"])))


def test_three_near_copies_become_one():
    trends = [_trend(-0.148, 70000, touches=5), _trend(-0.172, 69500, touches=3), _trend(-0.103, 70500, touches=3)]
    merged = merge_trends(trends, now=100, price_pct=2.0, slope_pct=0.08)
    assert len(merged) == 1
    assert merged[0]["touches"] == 5 and merged[0]["merged_from"] == 3      # the strongest survives


def test_trends_with_different_slopes_stay():
    trends = [_trend(-0.15, 70000), _trend(-0.60, 70000)]
    assert len(merge_trends(trends, now=100, price_pct=2.0, slope_pct=0.08)) == 2


def test_trends_far_apart_in_price_stay():
    trends = [_trend(-0.15, 70000), _trend(-0.15, 90000)]
    assert len(merge_trends(trends, now=100, price_pct=2.0, slope_pct=0.08)) == 2


def test_support_and_resistance_never_merge():
    trends = [_trend(-0.15, 70000, role="resistance"), _trend(-0.15, 70000, role="support")]
    assert len(merge_trends(trends, now=100, price_pct=2.0, slope_pct=0.08)) == 2


def test_the_survivor_keeps_the_longest_reach():
    trends = [_trend(-0.15, 70000, touches=4, first=10, last=100), _trend(-0.16, 70100, touches=4, first=0, last=95)]
    merged = merge_trends(trends, now=100, price_pct=2.0, slope_pct=0.08)[0]
    assert merged["first"] == 0 and merged["last"] == 100


def test_merging_off_and_empty():
    trends = [_trend(-0.15, 70000), _trend(-0.16, 70100)]
    assert merge_trends(trends, now=100, price_pct=0, slope_pct=0.08) == trends
    assert merge_trends([], now=100, price_pct=2.0, slope_pct=0.08) == []
