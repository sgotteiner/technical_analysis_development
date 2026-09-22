"""Tests for the no-lookahead timeframe aligner."""
import numpy as np
import pandas as pd
import pytest
from helpers.timestamp_helpers import align_timeframe_signal
from business_logic_services.strategy_service import StrategyService


def _df(index):
    return pd.DataFrame({"Close": range(len(index))}, index=pd.DatetimeIndex(index))


def test_daily_to_1h_uses_previous_completed_day():
    daily = _df(pd.date_range("2024-01-01", periods=3, freq="D"))
    signal = pd.Series([True, False, True], index=daily.index)  # per day
    hourly = _df(pd.date_range("2024-01-01 00:00", periods=72, freq="h"))

    out = align_timeframe_signal(daily, hourly, signal, fill_value=False)

    # Day 1 (Jan 1) bars: no completed daily bar yet -> fill_value False.
    assert not out[0] and not out[23]
    # Day 2 (Jan 2) bars: see Jan 1's completed value (True).
    assert out[24] and out[47]
    # Day 3 (Jan 3) bars: see Jan 2's completed value (False).
    assert not out[48] and not out[71]


def test_no_lookahead_htf_value_never_visible_within_its_own_bar():
    daily = _df(pd.date_range("2024-01-01", periods=5, freq="D"))
    signal = pd.Series([1, 2, 3, 4, 5], index=daily.index)
    hourly = _df(pd.date_range("2024-01-01 00:00", periods=120, freq="h"))

    out = align_timeframe_signal(daily, hourly, signal, fill_value=0.0)
    # A bar at 2024-01-03 12:00 must see day 2's value (2), never day 3's (3).
    idx = hourly.index.get_loc(pd.Timestamp("2024-01-03 12:00"))
    assert out[idx] == 2


def test_generalizes_to_1h_to_5m():
    h1 = _df(pd.date_range("2024-01-01 00:00", periods=3, freq="h"))
    signal = pd.Series([True, True, False], index=h1.index)
    m5 = _df(pd.date_range("2024-01-01 00:00", periods=36, freq="5min"))

    out = align_timeframe_signal(h1, m5, signal, fill_value=False)
    assert not out[0]                 # 00:00-00:55: nothing closed yet
    assert out[12] and out[23]        # 01:00-01:55: sees hour-0 (True)
    assert out[24]                    # 02:00: still sees hour-1 (True); hour-2 not closed
    assert out[30]                    # 02:30: last completed is hour-1 (True)


def test_output_length_and_order_match_ltf():
    daily = _df(pd.date_range("2024-01-01", periods=4, freq="D"))
    signal = pd.Series([True, False, True, False], index=daily.index)
    hourly = _df(pd.date_range("2024-01-01", periods=50, freq="h"))
    out = align_timeframe_signal(daily, hourly, signal, fill_value=False)
    assert len(out) == len(hourly)


def test_empty_inputs_return_fill():
    empty = pd.DataFrame()
    ltf = _df(pd.date_range("2024-01-01", periods=5, freq="h"))
    out = align_timeframe_signal(empty, ltf, pd.Series(dtype=bool), fill_value=False)
    assert len(out) == 5 and not out.any()


def test_registry_rejects_non_basestrategy():
    from strategies.base_strategy import BaseStrategy
    for name in StrategyService.list_available_strategies():
        inst = StrategyService.get_strategy_instance(name)
        assert isinstance(inst, BaseStrategy)
