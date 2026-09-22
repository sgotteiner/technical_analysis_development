"""Tests for the regime grader, using classifiers whose scores are known in advance."""
import numpy as np
import pandas as pd
import pytest
from business_logic_services.regime_grader import (grade, grade_batch, detection_lag, check_causal,
                                                   run_classifier)
from modules.data.market_regimes import RegimePeriod, BULL, BEAR, SIDEWAYS, STRAIGHT, GREAT
from modules.data.regime_batches import RegimeSet

LEAD = 30


def _set(regime, days=60, seed=0):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.02, LEAD + days)))
    idx = pd.date_range("2024-01-01", periods=LEAD + days, freq="D", tz="UTC")
    df = pd.DataFrame({"Open": close, "High": close, "Low": close, "Close": close, "Volume": 1.0}, index=idx)
    p = RegimePeriod(f"synthetic {regime}", regime, STRAIGHT, str(idx[LEAD].date()), str(idx[-1].date()), GREAT)
    return RegimeSet(p, df, LEAD)


def _constant(value):
    return lambda df: np.full(len(df), value)


def test_oracle_scores_perfectly():
    s = _set(BEAR)
    oracle = lambda df: np.where(np.arange(len(df)) >= LEAD, -1, 1)   # knows the label, bull before
    r = grade(oracle, [s])[0]
    assert r["agreement"] == 1.0 and r["opposite"] == 0.0
    assert r["lag_days"] == 0 and r["flips"] == 0 and r["days"] == 60


def test_always_bull_on_each_regime():
    bull, bear, side = grade(_constant(1), [_set(BULL), _set(BEAR), _set(SIDEWAYS)])
    assert bull["agreement"] == 1.0 and bull["opposite"] == 0.0
    assert bear["agreement"] == 0.0 and bear["opposite"] == 1.0
    assert side["agreement"] == 0.0 and side["opposite"] == 1.0      # any trend call counts against sideways
    assert side["lag_days"] is None


def test_late_classifier_lag_and_settle():
    states = np.array([0] * 10 + [1] * 50)
    r = grade_batch(states, BULL, settle=20, hold=5)
    assert r["lag_days"] == 10
    assert r["agreement"] == 1.0            # graded from day 20: all bull
    assert grade_batch(states, BULL, settle=0)["agreement"] == pytest.approx(50 / 60)


def test_lag_needs_the_label_held():
    states = np.array([1, 1, 0, 1, 1, 1, 1, 1, 0])
    assert detection_lag(states, 1, hold=5) == 3
    assert detection_lag(states, 1, hold=6) is None


def test_flips_and_shares():
    states = np.array([1, -1] * 30)
    r = grade_batch(states, BEAR, settle=0)
    assert r["flips"] == 59
    assert r["shares"] == {"bull": 0.5, "sideways": 0.0, "bear": 0.5}
    assert r["opposite"] == 0.5


def test_invalid_classifier_output_rejected():
    df = _set(BULL).df_daily
    with pytest.raises(ValueError):
        run_classifier(lambda d: np.ones(len(d) - 1), df)
    with pytest.raises(ValueError):
        run_classifier(lambda d: np.full(len(d), 2), df)


def test_check_causal_accepts_causal_and_catches_lookahead():
    df = _set(BULL, days=40).df_daily
    causal = lambda d: np.sign(d["Close"] - d["Close"].rolling(5, min_periods=1).mean()).to_numpy()
    peeking = lambda d: np.sign(d["Close"].shift(-1).fillna(d["Close"]) - d["Close"]).to_numpy()
    assert check_causal(causal, df, start=LEAD) == []
    assert len(check_causal(peeking, df, start=LEAD)) > 0
