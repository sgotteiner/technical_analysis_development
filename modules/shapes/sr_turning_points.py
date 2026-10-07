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


def turning_points(df: pd.DataFrame, threshold: float, on_closes: bool = False) -> Dict[str, np.ndarray]:
    """Alternating peaks/valleys: arrays idx (bar), kind (PEAK/VALLEY), y (log High/Low), conf.

    `on_closes`: the SWING is measured on closes, while the point keeps its own high/low, so a lone
    wick cannot make a turning point - his rule, "there was a candle who broke the support in a
    tail but got back and i ignored this spike" (2026-10-05).

    DEFAULT OFF, because it was measured and it loses. On his own three dated examples it finds
    5 of his 10 lines against 7 on highs/lows (at 9% and 12% size: 2 of 10). It does fix the case
    it was built for - at 2026-02-13 the 2026-02-06 candle (low 60,000, close 70,580, 17.6% above
    its own low) stops being a valley and the latest point becomes the 2026-01-14 peak at 97,924,
    the one he drew - but it moves enough other dots to cost more than it pays. Kept as a switch,
    not as the rule: the wick problem is real and needs a narrower answer than re-basing the whole
    zigzag.
    """
    high, low = np.log(df["High"].to_numpy()), np.log(df["Low"].to_numpy())
    if on_closes:
        swing_hi = swing_lo = np.log(df["Close"].to_numpy())
    else:
        swing_hi, swing_lo = high, low
    th = np.log(1 + threshold)
    # An extreme is never confirmed by its own candle: a daily bar does not say whether its high or
    # its low came first, so a bar wide enough to span the threshold would otherwise "reverse" from
    # its own high to its own low. That made a peak AND a valley on one date - 253 times at 7% - and
    # one candle then read as "a higher peak and a higher valley", turning his down trend at
    # 2026-09-04 into an up trend (owner, 2026-10-05: "the trend you drew is not even the same
    # direction as mine ... and doesnt have 2 peaks and valleys"). Dropping the second point of the
    # pair instead kept the wrong one: 2026-08-19 became a peak at 70,000 that nothing fell from.
    out = []                                   # (idx, kind, conf)
    direction, hi_i, lo_i = 0, 0, 0            # 0 unknown, +1 tracking a peak, -1 tracking a valley
    for i in range(1, len(high)):
        if direction == 0:
            hi_i = i if swing_hi[i] > swing_hi[hi_i] else hi_i
            lo_i = i if swing_lo[i] < swing_lo[lo_i] else lo_i
            if swing_hi[hi_i] - swing_lo[lo_i] >= th:
                # The first extreme only anchors the direction: nothing before it proves the
                # opposite move, so it is not a turning point itself.
                direction = 1 if hi_i > lo_i else -1
        elif direction == 1:
            hi_i = i if swing_hi[i] > swing_hi[hi_i] else hi_i
            if hi_i < i and swing_hi[hi_i] - swing_lo[i] >= th:
                out.append((hi_i, PEAK, i)); direction, lo_i = -1, i
        else:
            lo_i = i if swing_lo[i] < swing_lo[lo_i] else lo_i
            if lo_i < i and swing_hi[i] - swing_lo[lo_i] >= th:
                out.append((lo_i, VALLEY, i)); direction, hi_i = 1, i
    idx = np.array([p[0] for p in out], dtype=int)
    kind = np.array([p[1] for p in out], dtype=int)
    y = np.where(kind == PEAK, high[idx] if len(idx) else 0.0, low[idx] if len(idx) else 0.0)
    return {"idx": idx, "kind": kind, "y": np.asarray(y, dtype=float), "conf": np.array([p[2] for p in out], dtype=int)}
