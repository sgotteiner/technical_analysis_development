"""
Grades a trend classifier against the labelled regime batches (modules/data/regime_batches.py).

Classifier contract:
    classify(df_daily) -> array of len(df_daily), one state per day: +1 bull, 0 sideways, -1 bear.
    It must be causal: the state on day i may only use data up to and including day i.
    (check_causal verifies this by replaying the data day by day.)

Per batch it measures (batch = the labelled days, after the lead-in):
    agreement  share of graded days (from `settle` days in) whose state equals the label
    opposite   share of graded days called the opposite trend (bull<->bear); for sideways
               batches, the share called any trend
    shares     bull / sideways / bear share of graded days
    lag_days   days from the batch start until the label is first held for `hold` days in
               a row (None if never)
    flips      number of state changes inside the batch
"""
from typing import Callable, Dict, List, Optional
import numpy as np
import pandas as pd
from modules.data.market_regimes import BULL, BEAR

STATE = {BULL: 1, "sideways": 0, BEAR: -1}
Classifier = Callable[[pd.DataFrame], np.ndarray]


def run_classifier(classify: Classifier, df: pd.DataFrame) -> np.ndarray:
    states = np.asarray(classify(df))
    if states.shape != (len(df),):
        raise ValueError(f"classifier returned shape {states.shape}, expected ({len(df)},)")
    if not np.isin(states, (-1, 0, 1)).all():
        raise ValueError("classifier states must be -1, 0 or +1")
    return states.astype(int)


def detection_lag(states: np.ndarray, label: int, hold: int) -> Optional[int]:
    """First day index at which `label` starts a run of at least `hold` consecutive days."""
    run = 0
    for i, s in enumerate(states):
        run = run + 1 if s == label else 0
        if run == hold:
            return i - hold + 1
    return None


def grade_batch(states: np.ndarray, regime: str, settle: int = 20, hold: int = 5) -> Dict:
    label = STATE[regime]
    graded = states[settle:]
    shares = {name: float(np.mean(graded == v)) for name, v in STATE.items()}
    opposite = float(np.mean(graded == -label)) if label else float(np.mean(graded != 0))
    return {
        "agreement": float(np.mean(graded == label)),
        "opposite": opposite,
        "shares": shares,
        "lag_days": detection_lag(states, label, hold),
        "flips": int(np.sum(states[1:] != states[:-1])),
    }


def grade(classify: Classifier, sets: List, settle: int = 20, hold: int = 5) -> List[Dict]:
    """Grade the classifier on every batch; each set brings its own lead-in history."""
    reports = []
    for s in sets:
        states = run_classifier(classify, s.df_daily)[s.start_daily:]
        report = grade_batch(states, s.period.regime, settle, hold)
        report.update(name=s.period.name, regime=s.period.regime, shape=s.period.shape, days=len(states))
        reports.append(report)
    return reports


def check_causal(classify: Classifier, df: pd.DataFrame, start: int, stride: int = 1) -> List[int]:
    """Row positions (from `start`) where the live answer (data up to that row only)
    differs from the answer computed on the full data. Empty list = no lookahead."""
    full = run_classifier(classify, df)
    return [i for i in range(start, len(df), stride)
            if run_classifier(classify, df.iloc[:i + 1])[i] != full[i]]
