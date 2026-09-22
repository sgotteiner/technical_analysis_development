"""Tests for the block-composition orchestrator."""
import numpy as np
import pandas as pd
import pytest
from modules.base import BaseBlock, BlockResult
from strategies.composable_strategy import ComposableStrategy


class FakeBlock(BaseBlock):
    """A block that returns a fixed native-timeframe mask."""
    def __init__(self, tf, mask, name="fake"):
        super().__init__(name=name, category="Test", tf=tf)
        self._mask = np.asarray(mask)

    def evaluate(self, df_daily, df_1h):
        return BlockResult(self.name, self.category, self.tf, self._mask)


def _daily(n):
    return pd.DataFrame({"Close": range(n)}, index=pd.date_range("2024-01-01", periods=n, freq="D"))


def _hourly(n):
    return pd.DataFrame({"Close": range(n)}, index=pd.date_range("2024-01-01", periods=n, freq="h"))


def test_daily_trend_block_aligned_no_lookahead():
    df_d, df_1h = _daily(3), _hourly(72)
    strat = ComposableStrategy("t", trend_blocks=[FakeBlock("1D", [True, False, True])])
    signals, macro, _ = strat.generate_signals(df_d, df_1h)
    assert not macro[0] and not macro[23]   # day1: nothing closed yet
    assert macro[24] and macro[47]          # day2 sees day1 (True)
    assert not macro[48] and not macro[71]  # day3 sees day2 (False)


def test_hourly_block_passthrough_not_shifted():
    df_d, df_1h = _daily(3), _hourly(5)
    mask = [True, False, True, False, True]
    strat = ComposableStrategy("t", trend_blocks=[FakeBlock("1H", mask)])
    _, macro, _ = strat.generate_signals(df_d, df_1h)
    assert list(macro) == mask   # 1H block used as-is, no shift


def test_combine_all_vs_any_vs_n():
    df_d, df_1h = _daily(2), _hourly(4)
    a = FakeBlock("1H", [True, True, False, False], "a")
    b = FakeBlock("1H", [True, False, True, False], "b")

    all_s = ComposableStrategy("all", entry_blocks=[a, b], combine="ALL")
    any_s = ComposableStrategy("any", entry_blocks=[a, b], combine="ANY")
    n2_s = ComposableStrategy("n2", entry_blocks=[a, b], combine=2)

    assert list(all_s.generate_signals(df_d, df_1h)[0]) == [1, 0, 0, 0]  # AND
    assert list(any_s.generate_signals(df_d, df_1h)[0]) == [1, 1, 1, 0]  # OR
    assert list(n2_s.generate_signals(df_d, df_1h)[0]) == [1, 0, 0, 0]   # 2-of-2


def test_regime_gates_entry():
    df_d, df_1h = _daily(2), _hourly(4)
    trend = FakeBlock("1H", [True, True, False, False], "trend")
    entry = FakeBlock("1H", [True, True, True, True], "entry")
    strat = ComposableStrategy("g", trend_blocks=[trend], entry_blocks=[entry], combine="ANY")
    signals, _, _ = strat.generate_signals(df_d, df_1h)
    assert list(signals) == [1, 1, 0, 0]   # entry only fires where regime is bull


def test_no_blocks_defaults_to_always_bull():
    df_d, df_1h = _daily(2), _hourly(4)
    strat = ComposableStrategy("empty")
    signals, macro, _ = strat.generate_signals(df_d, df_1h)
    assert macro.all() and list(signals) == [1, 1, 1, 1]
