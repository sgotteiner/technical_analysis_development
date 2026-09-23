"""
Tests for the bull-flag finder (modules/shapes/bull_flag.py): a fast rise (the pole) and then a
shallow pause just below its top (the flag), ending at bar `end`. Uses bars <= end only.
Thresholds are Claude's, read from the owner's first drawn flag (BTC 2026-08-15..09-04: pole
+27% in 5 days, pause of 2 weeks, retrace ~25%, drifting up to ~3% above the pole top).
"""
import numpy as np
import pytest
from modules.shapes.bull_flag import bull_flag_at
from setup_charts import df_from_close, legs

POLE_FLAG = [(80, 10), (104, 5), (98, 3), (103, 3), (99, 2), (102, 3)]      # base 80, pole to 104


def test_finds_the_pole_and_the_flag():
    df = df_from_close(legs(80, POLE_FLAG))
    f = bull_flag_at(df, len(df) - 1)
    assert f is not None
    assert f["pole_start"] == 10 and f["pole_top"] == 15
    assert f["pole_low"] == pytest.approx(80) and f["pole_high"] == pytest.approx(104)
    assert f["flag_low"] == pytest.approx(98) and f["flag_high"] == pytest.approx(104)


def test_a_small_rise_is_not_a_pole():
    df = df_from_close(legs(80, [(80, 10), (88, 5), (85, 3), (87, 3), (86, 3)]))       # +10%
    assert bull_flag_at(df, len(df) - 1) is None


def test_a_deep_pullback_is_not_a_flag():
    df = df_from_close(legs(80, [(80, 10), (104, 5), (86, 5), (90, 3)]))               # gives back 75%
    assert bull_flag_at(df, len(df) - 1) is None


def test_price_far_above_the_pole_top_is_no_longer_a_flag():
    df = df_from_close(legs(80, [(80, 10), (104, 5), (100, 6), (101, 3), (112, 2)]))   # 8% above the top
    assert bull_flag_at(df, len(df) - 1) is None


def test_a_pause_that_lasts_too_long_is_not_a_flag():
    df = df_from_close(legs(80, [(80, 10), (104, 5)] + [(99, 4), (103, 4)] * 6))       # 48 bars
    assert bull_flag_at(df, len(df) - 1) is None


def test_the_flag_needs_a_few_bars():
    df = df_from_close(legs(80, [(80, 10), (104, 5), (102, 1)]))
    assert bull_flag_at(df, len(df) - 1) is None


def test_no_lookahead_and_scale_invariance():
    rng = np.random.default_rng(3)
    close = 100 * np.exp(np.cumsum(rng.normal(0.002, 0.03, 400)))
    df = df_from_close(close, wick=0.01)
    for end in range(60, 400, 7):
        assert bull_flag_at(df, end) == bull_flag_at(df.iloc[:end + 1], end), end
    a, b = bull_flag_at(df, 399), bull_flag_at(df * 3, 399)
    assert (a is None) == (b is None)
    if a:
        assert a["pole_top"] == b["pole_top"] and b["pole_high"] == pytest.approx(3 * a["pole_high"])
