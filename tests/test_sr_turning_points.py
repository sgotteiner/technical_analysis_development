"""
Tests for turning points (modules/shapes/sr_turning_points.py): peaks and valleys by MAGNITUDE.
A valley is the low between a >= threshold fall and a >= threshold rise; a peak the reverse.
Each point is known only once the reversal has happened (its confirmation bar) - no lookahead.
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.sr_turning_points import turning_points, PEAK, VALLEY


def _df(close):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2022-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def test_finds_peaks_and_valleys_of_at_least_the_threshold():
    close = [100, 95, 90, 100, 110, 120, 110, 100, 105, 99, 90, 100, 115, 130]
    tp = turning_points(_df(close), threshold=0.10)
    assert list(zip(tp["idx"], tp["kind"])) == [(2, VALLEY), (5, PEAK), (10, VALLEY)]
    assert list(tp["conf"]) == [3, 7, 11]              # the bar where the >=10% reversal happened


def test_small_wiggles_are_not_turning_points():
    close = [100, 104, 101, 105, 102, 106, 103, 107]    # 3-4% moves only
    assert len(turning_points(_df(close), threshold=0.10)["idx"]) == 0


def test_points_alternate_and_are_the_extremes_between_reversals():
    rng = np.random.default_rng(3)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, 400)))
    df = _df(close)
    tp = turning_points(df, threshold=0.10)
    kinds, idx = tp["kind"], tp["idx"]
    assert (kinds[1:] != kinds[:-1]).all()
    y = np.log(close)
    for a, b, k in zip(idx[:-1], idx[1:], kinds[:-1]):
        seg = y[a:b + 1]
        assert y[a] == (seg.max() if k == PEAK else seg.min())   # a peak is the highest point until the next valley


def test_legs_are_at_least_the_threshold():
    rng = np.random.default_rng(4)
    tp = turning_points(_df(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 400)))), threshold=0.10)
    assert (np.abs(np.diff(tp["y"])) >= np.log(1.10) - 1e-12).all()


def test_no_lookahead_prefix_is_identical():
    """Points confirmed by bar e are the same whether or not later bars exist."""
    rng = np.random.default_rng(5)
    df = _df(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 300))))
    full = turning_points(df, threshold=0.10)
    for e in range(50, 300, 17):
        cut = turning_points(df.iloc[:e + 1], threshold=0.10)
        keep = full["conf"] <= e
        for key in ("idx", "kind", "conf"):
            assert list(cut[key]) == list(full[key][keep]), (e, key)


def test_scale_invariant():
    rng = np.random.default_rng(6)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, 300)))
    a, b = turning_points(_df(close), 0.10), turning_points(_df(close * 7), 0.10)
    assert list(a["idx"]) == list(b["idx"]) and list(a["kind"]) == list(b["kind"])
