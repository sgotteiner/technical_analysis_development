"""Tests for period metrics on series whose answers are known by construction."""
import numpy as np
import pandas as pd
import pytest
from helpers.regime_metrics import period_metrics, flat_steps, range_touches


def _df(close, high=None, low=None):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2024-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c if high is None else high,
                         "Low": c if low is None else low, "Close": c}, index=idx)


def test_straight_exponential_uptrend():
    m = period_metrics(_df(100 * 1.01 ** np.arange(31)))   # +1% every day for 30 days
    assert m["return"] == pytest.approx(1.01 ** 30 - 1)
    assert m["days"] == 30                                   # 31 bars span 30 days
    assert m["per_month"] == pytest.approx(1.01 ** 30 - 1)  # exactly one 30-day month
    assert m["efficiency"] == pytest.approx(1.0)
    assert m["r2"] == pytest.approx(1.0)
    assert m["up_days"] == 1.0
    assert m["max_pullback"] == pytest.approx(0.0)
    assert m["pullbacks_10"] == 0
    assert m["best_day"] == pytest.approx(0.01) and m["worst_day"] == pytest.approx(0.01)


def test_round_trip_has_zero_efficiency():
    m = period_metrics(_df([100, 110, 121, 110, 100]))
    assert m["return"] == pytest.approx(0.0)
    assert m["efficiency"] == pytest.approx(0.0, abs=1e-12)
    assert m["max_bounce"] == pytest.approx(0.21)
    assert m["max_pullback"] == pytest.approx(1 - 100 / 121)


def test_efficiency_is_net_over_path():
    # up 10%, down 10%, up 10% (in log terms): net = 1 unit, path = 3 units
    r = np.log(1.1)
    close = 100 * np.exp(np.cumsum([0, r, -r, r]))
    assert period_metrics(_df(close))["efficiency"] == pytest.approx(1 / 3)


def test_pullback_and_bounce_episode_counts():
    # two separate >10% drops (each followed by a new high), one 5% drop that must not count
    close = [100, 120, 105, 125, 110, 130, 124, 135]
    m = period_metrics(_df(close))
    assert m["pullbacks_10"] == 2
    assert m["max_pullback"] == pytest.approx(1 - 105 / 120)
    down = [200, 150, 170, 140, 145, 120]           # bounces from lows: +13% and +3.6%
    assert period_metrics(_df(down))["bounces_10"] == 1


def test_volatility_and_trend_noise():
    r = 0.02
    close = 100 * np.exp(np.cumsum([0] + [r, -r] * 50))   # alternating +-2% log moves
    m = period_metrics(_df(close))
    assert m["volatility"] == pytest.approx(r * np.sqrt(365))
    assert m["trend_noise"] == pytest.approx(0.0, abs=1e-12)
    assert m["up_days"] == 0.5


def test_flat_steps_counts_non_overlapping_flat_stretches():
    up = list(100 * 1.02 ** np.arange(30))              # rising 2%/day: no flat stretch
    step = [up[-1]] * 25                                # 25 flat days -> one 21-day step
    up2 = list(step[-1] * 1.02 ** np.arange(1, 30))
    close = np.array(up + step + up2 + [up2[-1]] * 45)  # 45 flat days -> two more steps
    assert flat_steps(close) == 3
    assert flat_steps(np.array(up)) == 0


def test_range_touches_counts_alternating_zone_visits():
    osc = 100 + 10 * np.sin(np.linspace(0, 4 * np.pi, 200))   # two full cycles: T,B,T,B
    assert range_touches(osc) == 4
    assert range_touches(np.linspace(100, 150, 50)) == 2      # a trend touches bottom then top
    m = period_metrics(_df(osc))
    assert m["touches"] == 4 and m["band"] == pytest.approx(osc.max() / osc.min())


def test_flat_series_is_defined_not_nan():
    m = period_metrics(_df([100.0] * 10))
    assert m["efficiency"] == 0.0 and m["r2"] == 0.0 and m["trend_noise"] == 0.0
    assert all(np.isfinite(v) for v in m.values())


def test_true_range_uses_gaps():
    close = np.array([100, 100, 100.0])
    high = np.array([100, 102, 101.0])
    low = np.array([100, 99, 100.0])
    # day 2: range 3 -> 3%; day 3: max(1, |101-100|, |100-100|) = 1 -> 1%
    assert period_metrics(_df(close, high, low))["atr_pct"] == pytest.approx(0.02)
