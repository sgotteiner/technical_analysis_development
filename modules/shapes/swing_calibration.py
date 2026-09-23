"""
Swing calibration (owner's idea, 2026-09-23): a trader is defined by how long a trade takes, so
the swing size to look for is the one whose legs last about that long. "2 weeks on BTC" measures
~12% on recent data; the same 10% leg took 2 days in 2017-2023 and 8 days now, so the size is
calibrated from the data BEFORE `end`, never fixed.

Ties (several sizes give legs of the same length) go to the LARGEST size: the biggest swing that
still moves at that pace.
"""
from typing import Dict
import numpy as np
import pandas as pd
from modules.shapes.sr_turning_points import turning_points

LOOKBACK = 730          # days of history the calibration looks at
MIN_LEGS = 6            # fewer legs than this says nothing
GRID = np.round(np.arange(0.03, 0.3001, 0.005), 4)


def leg_stats(df: pd.DataFrame, end: int, size: float, lookback: int = LOOKBACK) -> Dict:
    """How long the legs of a `size` zigzag last, over the `lookback` days up to `end`."""
    window = df.iloc[max(0, end - lookback + 1):end + 1]
    tp = turning_points(window, size)
    if len(tp["idx"]) < 2:
        return {"legs": 0, "median_days": None, "mean_days": None, "median_size": None}
    days, sizes = np.diff(tp["idx"]), np.abs(np.diff(tp["y"]))
    return {"legs": int(len(days)), "median_days": float(np.median(days)), "mean_days": float(np.mean(days)),
            "median_size": float(np.median(sizes))}


def calibrate_size(df: pd.DataFrame, end: int, target_days: float, lookback: int = LOOKBACK) -> Dict:
    """The swing size whose median leg is closest to `target_days` (ties -> the largest size)."""
    best = {"size": None, "median_days": None, "legs": 0, "target_days": target_days}
    best_gap = None
    for size in GRID:
        st = leg_stats(df, end, float(size), lookback)
        if st["legs"] < MIN_LEGS:
            continue
        gap = abs(st["median_days"] - target_days)
        if best_gap is None or gap <= best_gap:
            best_gap = gap
            best = {"size": float(size), "median_days": st["median_days"], "legs": st["legs"],
                    "median_size": st["median_size"], "target_days": target_days}
    return best
