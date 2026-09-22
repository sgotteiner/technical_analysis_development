"""Unit tests for TrendClassifierBlock on synthetic series with known answers."""
import numpy as np
import pandas as pd
import pytest
from modules.trends.trend_classifier import TrendClassifierBlock, hold_states, rolling_efficiency, BULL, BEAR, SIDEWAYS


def _df(close):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2020-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": 1.0}, index=idx)


def _state(close, **kw):
    return TrendClassifierBlock("1D", **kw).evaluate(_df(close), None).metadata["state"]


def _noisy(drift, n=300, seed=0, vol=0.01):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(drift + rng.normal(0, vol, n)))


def test_steady_uptrend_is_bull():
    assert (_state(_noisy(0.01))[100:] == BULL).all()


def test_steady_downtrend_is_bear():
    assert (_state(_noisy(-0.01))[100:] == BEAR).all()


def test_flat_market_is_sideways():
    assert (_state(_noisy(0.0, vol=0.005))[100:] == SIDEWAYS).mean() > 0.9


def test_range_with_swings_shorter_than_patience_is_sideways():
    t = np.arange(400)
    rng = np.random.default_rng(1)
    close = 100 * np.exp(0.12 * np.sin(2 * np.pi * t / 30) + rng.normal(0, 0.01, 400))  # +-12%, 30-day cycle
    assert (_state(close)[150:] == SIDEWAYS).mean() > 0.8


def test_range_with_legs_longer_than_patience_reads_as_trends():
    """Known limit: a smooth 40-day +-30% leg IS a trend at 30-day patience."""
    t = np.arange(400)
    close = 100 * np.exp(0.15 * np.sin(2 * np.pi * t / 80))      # +-15% swings, 80-day cycle
    states = _state(close)[150:]
    assert (states == BULL).mean() > 0.3 and (states == BEAR).mean() > 0.3


def test_no_lookahead_live_replay():
    df = _df(_noisy(0.001, n=250, seed=3, vol=0.03))
    blk = TrendClassifierBlock("1D")
    full = blk.evaluate(df, None).metadata["state"]
    live = [blk.evaluate(df.iloc[:i + 1], None).metadata["state"][i] for i in range(len(df))]
    assert (np.array(live) == full).all()


def test_hold_states_needs_consecutive_days():
    raw = np.array([1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1])
    assert hold_states(raw, 3).tolist() == [1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0]
    assert hold_states(raw, 1).tolist() == raw.tolist()


def test_rolling_efficiency_straight_and_round_trip():
    straight = pd.Series(100 * 1.01 ** np.arange(30))
    assert rolling_efficiency(straight, 10).iloc[-1] == pytest.approx(1.0)
    zigzag = pd.Series([100, 110] * 15, dtype=float)
    assert rolling_efficiency(zigzag, 10).iloc[-1] == pytest.approx(0.0)


def test_metadata_explains_each_day():
    res = TrendClassifierBlock("1D").evaluate(_df(_noisy(0.01)), None)
    meta = res.metadata
    for key in ("state", "raw_state", "votes", "move_n", "efficiency_n", "going_nowhere"):
        assert len(meta[key]) == 300, key
    assert (res.mask == (meta["state"] == BULL)).all()
    assert set(np.unique(meta["votes"])) <= {-3, -2, -1, 0, 1, 2, 3}
