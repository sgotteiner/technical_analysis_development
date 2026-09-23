"""
Tests for swing calibration (modules/shapes/swing_calibration.py). The owner's idea (2026-09-23):
a trader is defined by how long a trade takes, so the swing size to look for is the one whose legs
last about that long ("2 weeks on BTC" measured ~12% on recent data). Calibrated from the data
before `end` only, because volatility changes: a 10% leg took 2 days in 2017-2023 and 8 days now.
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.swing_calibration import calibrate_size, leg_stats
from setup_charts import df_from_close, legs


def _zigzag(swing, bars, n=40, base=100.0):
    """n legs of `swing` (log) each taking `bars` bars."""
    moves = []
    for i in range(n):
        moves.append((base * np.exp(swing * (i % 2 == 0)), bars))
    return df_from_close(legs(base, moves))


def test_leg_stats_measure_length_and_size():
    df = _zigzag(np.log(1.2), 10)
    st = leg_stats(df, len(df) - 1, 0.15, lookback=400)
    assert st["legs"] >= 20 and st["median_days"] == pytest.approx(10, abs=1)
    assert st["median_size"] == pytest.approx(np.log(1.2), rel=0.02)


def test_calibration_finds_the_size_whose_legs_last_the_target():
    for swing, bars in ((np.log(1.2), 10), (np.log(1.1), 4)):
        df = _zigzag(swing, bars)
        got = calibrate_size(df, len(df) - 1, target_days=bars)
        assert got["size"] == pytest.approx(np.expm1(swing), abs=0.02), (swing, bars, got)
        assert got["median_days"] == pytest.approx(bars, abs=1)


def test_a_longer_target_asks_for_a_bigger_size():
    rng = np.random.default_rng(7)
    df = df_from_close(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 800))), wick=0.005)
    sizes = [calibrate_size(df, 799, target_days=d)["size"] for d in (3, 7, 14, 30)]
    assert all(a <= b for a, b in zip(sizes, sizes[1:])), sizes


def test_calibration_uses_only_the_past():
    rng = np.random.default_rng(8)
    df = df_from_close(100 * np.exp(np.cumsum(rng.normal(0, 0.02, 900))), wick=0.005)
    for end in (500, 700, 899):
        assert calibrate_size(df, end, 14) == calibrate_size(df.iloc[:end + 1], end, 14), end


def test_too_little_history_gives_no_size():
    df = df_from_close(100 * np.exp(np.cumsum(np.random.default_rng(9).normal(0, 0.02, 30))))
    assert calibrate_size(df, 29, target_days=14)["size"] is None
