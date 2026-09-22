"""Tests for the market-structure regime block: no lookahead + correct bull/bear/sideways."""
import numpy as np
import pandas as pd
import pytest
from modules.trends.market_structure import MarketStructureBlock, BULL, BEAR, SIDEWAYS


def _df(close, spread=0.002):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2020-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c * (1 + spread), "Low": c * (1 - spread),
                         "Close": c, "Volume": np.ones(len(c))}, index=idx)


def _zigzag(n, slope, leg=10, amp=10.0, base=100.0):
    i = np.arange(n)
    tri = np.abs((i % (2 * leg)) - leg)          # 0..leg..0 triangle wave
    return base + slope * i + amp * tri / leg


def _random_walk(n, seed):
    rng = np.random.default_rng(seed)
    return 100 * np.exp(np.cumsum(rng.normal(0, 0.03, n)))


def _states(df, span=5):
    return MarketStructureBlock("1D", pivot_span=span).evaluate(df, None).metadata["state"]


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_live_replay_matches_backtest(seed):
    """Every bar's state must equal what the block said live, using only data up to that bar."""
    df = _df(_random_walk(300, seed))
    full = _states(df)
    live = np.array([_states(df.iloc[:i + 1])[i] for i in range(len(df))])
    assert (live == full).all()


def test_future_changes_do_not_alter_past():
    df = _df(_random_walk(300, 7))
    before = _states(df)
    shocked = df.copy()
    shocked.iloc[200:, :4] *= np.random.default_rng(0).uniform(0.5, 1.5, (100, 1))
    assert (_states(shocked)[:200] == before[:200]).all()


def test_swing_confirmed_only_after_span_bars():
    blk = MarketStructureBlock("1D", pivot_span=5)
    df = _df(_zigzag(80, 0.0))
    sh, sl = blk.find_pivots(df["High"].values, df["Low"].values)
    assert sh and sl
    assert all(conf == p + 5 for p, _, conf in sh + sl)


def test_uptrend_is_bull():
    assert _states(_df(_zigzag(200, 0.5)))[-1] == BULL


def test_downtrend_is_bear():
    assert _states(_df(_zigzag(200, -0.5, base=300.0)))[-1] == BEAR


def test_flat_range_is_sideways():
    s = _states(_df(_zigzag(200, 0.0)))
    assert (s[60:] == SIDEWAYS).all()


def test_not_ready_until_two_swings_each_side():
    res = MarketStructureBlock("1D").evaluate(_df(_zigzag(200, 0.5)), None)
    ready, state = res.metadata["ready"], res.metadata["state"]
    assert not ready[:15].any() and ready[-1]
    assert (state[~ready] == SIDEWAYS).all()


def test_mask_is_bull_state():
    res = MarketStructureBlock("1D").evaluate(_df(_random_walk(300, 4)), None)
    assert (res.mask == (res.metadata["state"] == BULL)).all()


@pytest.mark.parametrize("close,expected", [
    (125, BULL),       # breaks above last swing high, even though structure is bearish
    (85, BEAR),        # breaks below last swing low, even though structure is bullish
])
def test_break_of_structure_takes_priority(close, expected):
    if expected == BULL:
        args = (close, 130, 120, 100, 90)   # LH + LL structure
    else:
        args = (close, 110, 120, 80, 90)    # HH + HL structure
    assert MarketStructureBlock.classify(*args) == expected


def test_classify_structure_without_break():
    assert MarketStructureBlock.classify(105, 110, 120, 80, 90) == BULL      # HH + HL
    assert MarketStructureBlock.classify(105, 130, 120, 100, 90) == BEAR     # LH + LL
    assert MarketStructureBlock.classify(105, 110, 120, 100, 90) == SIDEWAYS  # HH + LL
