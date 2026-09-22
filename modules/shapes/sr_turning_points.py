"""
Turning points by magnitude (owner, 2026-09-22): a peak is the high between a rise of at least
`threshold` and a fall of at least `threshold`; a valley is the reverse (a % zigzag on log price).

A point is known only once the reversal has happened: its confirmation bar `conf` is the bar
where price had moved `threshold` away from it. Every decision uses bars <= the current bar, so
the points confirmed by any bar e are identical whether or not later bars exist (no lookahead).
"""
from typing import Dict
import numpy as np
import pandas as pd

PEAK, VALLEY = 1, -1


def turning_points(df: pd.DataFrame, threshold: float) -> Dict[str, np.ndarray]:
    """Alternating peaks/valleys: arrays idx (bar), kind (PEAK/VALLEY), y (log High/Low), conf."""
    high, low = np.log(df["High"].to_numpy()), np.log(df["Low"].to_numpy())
    th = np.log(1 + threshold)
    out = []                                   # (idx, kind, conf)
    direction, hi_i, lo_i = 0, 0, 0            # 0 unknown, +1 tracking a peak, -1 tracking a valley
    for i in range(1, len(high)):
        if direction == 0:
            hi_i = i if high[i] > high[hi_i] else hi_i
            lo_i = i if low[i] < low[lo_i] else lo_i
            if high[hi_i] - low[lo_i] >= th:
                # The first extreme only anchors the direction: nothing before it proves the
                # opposite move, so it is not a turning point itself.
                direction = 1 if hi_i > lo_i else -1
        elif direction == 1:
            hi_i = i if high[i] > high[hi_i] else hi_i
            if high[hi_i] - low[i] >= th:
                out.append((hi_i, PEAK, i)); direction, lo_i = -1, i
        else:
            lo_i = i if low[i] < low[lo_i] else lo_i
            if high[i] - low[lo_i] >= th:
                out.append((lo_i, VALLEY, i)); direction, hi_i = 1, i
    idx = np.array([p[0] for p in out], dtype=int)
    kind = np.array([p[1] for p in out], dtype=int)
    y = np.where(kind == PEAK, high[idx] if len(idx) else 0.0, low[idx] if len(idx) else 0.0)
    return {"idx": idx, "kind": kind, "y": np.asarray(y, dtype=float), "conf": np.array([p[2] for p in out], dtype=int)}
