"""Tests for the honest bench: block causality, intrabar stop, drawdown, explainer."""
import numpy as np
import pandas as pd
import pytest
from modules.trends.supertrend import SuperTrendBlock
from utils.calculation_utils import calculate_max_drawdown
from business_logic_services.backtest_service import BacktestService
from business_logic_services.explain import explain_result


def _ohlc(closes):
    idx = pd.date_range("2024-01-01", periods=len(closes), freq="h", tz="UTC")
    c = np.array(closes, dtype=float)
    return pd.DataFrame({"Open": c, "High": c * 1.001, "Low": c * 0.999,
                         "Close": c, "Volume": np.ones(len(c))}, index=idx)


class _FakeCycle:
    def __init__(self, df_1h, bnh=0.0):
        self.df_1h = df_1h
        self.df_daily = df_1h
        self.name = "test"
        self.start_date = "2024-01-01"
        self.end_date = "2024-02-01"
        self.bnh_return = bnh


class _AlwaysLong:
    """Trivial trusted strategy: always in the market (regime always bull, always signal)."""
    name = "always-long"
    params = {"stop_loss_pct": 0.10}

    def generate_signals(self, df_daily, df_1h):
        n = len(df_1h)
        return np.ones(n, dtype=int), np.ones(n, dtype=bool), {}


def test_supertrend_block_is_causal():
    """A causal block's past output must not change when future bars change."""
    base = _ohlc(list(range(100, 200)))
    blk = SuperTrendBlock(tf="1H")
    m1 = np.asarray(blk.evaluate(base, base).mask)
    tampered = base.copy()
    tampered.iloc[60:] *= 5.0                      # rewrite the future
    m2 = np.asarray(blk.evaluate(tampered, tampered).mask)
    assert np.array_equal(m1[:50], m2[:50])        # first 50 bars unchanged


def test_intrabar_stop_fires_on_low_not_close():
    # price closes flat but one bar's LOW pierces the 10% stop -> must exit at stop
    closes = [100.0] * 10
    df = _ohlc(closes)
    df.iloc[5, df.columns.get_loc("Low")] = 85.0   # -15% wick on bar 5
    res = BacktestService.execute_backtest(_AlwaysLong(), _FakeCycle(df), 1000.0, verbose=False)
    t = res["trades_list"][0]
    assert t["ExitReason"] == "stop"
    assert t["ReturnPct"] == pytest.approx(-0.10, abs=1e-6)


def test_max_drawdown():
    assert calculate_max_drawdown([100, 120, 60, 90]) == pytest.approx(50.0)  # 120 -> 60
    assert calculate_max_drawdown([100, 110, 120]) == pytest.approx(0.0)


def test_mae_mfe_recorded():
    closes = [100.0, 110.0, 90.0, 100.0]
    res = BacktestService.execute_backtest(_AlwaysLong(), _FakeCycle(_ohlc(closes)), 1000.0, verbose=False)
    t = res["trades_list"][0]
    assert t["MFE"] > 0.09 and t["MAE"] < -0.09     # saw +10% and -10% intrabar


def test_explainer_shape():
    closes = [100.0, 105.0, 110.0, 108.0]
    res = BacktestService.execute_backtest(_AlwaysLong(), _FakeCycle(_ohlc(closes)), 1000.0, verbose=False)
    exp = explain_result(res)
    assert "by_exit_reason" in exp and "give_back" in exp and "risk" in exp
    assert exp["give_back"]["avg_capture_of_peak"] <= 1.01
