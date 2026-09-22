import numpy as np
import pandas as pd
from modules.base import BaseBlock, BlockResult

BULL, SIDEWAYS, BEAR = 1, 0, -1


def rolling_efficiency(close: pd.Series, n: int) -> pd.Series:
    """|net log move| / sum of |daily log moves| over the last n days (1 = straight line)."""
    lr = np.log(close).diff()
    return (lr.rolling(n).sum().abs() / lr.abs().rolling(n).sum()).fillna(0.0)


def hold_states(raw: np.ndarray, hold: int) -> np.ndarray:
    """Switch to a new state only after it has been the raw state `hold` days in a row."""
    out = np.empty(len(raw), dtype=int)
    current, candidate, run = raw[0], raw[0], 0
    for i, r in enumerate(raw):
        if r == current:
            run = 0
        else:
            run = run + 1 if r == candidate else 1
            candidate = r
            if run >= hold:
                current, run = r, 0
        out[i] = current
    return out


class TrendClassifierBlock(BaseBlock):
    """
    Category 1: Trend Classifier (market regime: bull / bear / sideways)

    Built from sub-parts, each answering one question on daily closes (all causal):
      1. direction  - did price rise or fall over n/2, n and 2n days? each lookback votes +1/-1
      2. going nowhere - is price back within `move_min` of where it was n days ago,
                         or was the n-day path inefficient (efficiency < `eff_min`)?
      3. raw state  - going nowhere -> SIDEWAYS, else the majority vote (BULL / BEAR)
      4. persistence - the state changes only after the new raw state holds `hold` days

    `n` is the patience: how long price must go nowhere before it counts as sideways.
    Graded against the regime answer key in tests/test_trend_classifiers.py. Known limit:
    a stair step and the start of a flat look the same without hindsight, so stairs trends
    are often read as sideways during their steps.

    mask = (state == BULL). metadata holds every sub-part per day for explainability.
    """
    def __init__(self, tf='1D', n=30, move_min=0.10, eff_min=0.10, hold=5):
        super().__init__(name=f"Trend Classifier ({tf} n={n})", category="Trend", tf=tf)
        self.n, self.move_min, self.eff_min, self.hold = n, move_min, eff_min, hold

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        close = df['Close']
        lookbacks = (self.n // 2, self.n, 2 * self.n)

        votes = sum(np.sign(np.log(close / close.shift(k))).fillna(0.0) for k in lookbacks).to_numpy()
        move_n = np.log(close / close.shift(self.n)).to_numpy()
        eff_n = rolling_efficiency(close, self.n).to_numpy()
        nowhere = (np.abs(np.nan_to_num(move_n, nan=0.0)) < self.move_min) | (eff_n < self.eff_min)

        direction = np.where(votes >= 1, BULL, np.where(votes <= -1, BEAR, SIDEWAYS))
        raw = np.where(nowhere, SIDEWAYS, direction)
        state = hold_states(raw, self.hold)

        # Native-timeframe mask; alignment is owned by the strategy orchestrator.
        return BlockResult(self.name, self.category, self.tf, state == BULL, metadata={
            "state": state, "raw_state": raw, "votes": votes,
            "move_n": move_n, "efficiency_n": eff_n, "going_nowhere": nowhere,
        })
