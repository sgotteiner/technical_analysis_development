"""
Bull flag ending at bar `end`: a fast rise (the pole) and a shallow pause just below its top (the
flag). Uses bars <= end only, so it can be run live.

  pole top    the highest high in [end - flag_max_bars, end - flag_min_bars]
  pole start  the last lowest low in the pole_max_bars before the top (where the rise began)
  pole        rise >= pole_min_rise (log)
  flag        the bars after the top up to `end`: gives back <= max_retrace of the pole, and never
              goes more than max_over_top above the top (then it is a new rally, not a pause)

Thresholds are Claude's, read from the owner's first drawn flag (BTC 2026-08-15..09-04: pole
+27% in 5 days, pause of two weeks giving back ~25%, drifting ~3% above the pole top).
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd

FLAG = {"pole_min_rise": 0.15, "pole_max_bars": 15, "flag_min_bars": 3, "flag_max_bars": 25,
        "max_retrace": 0.5, "max_over_top": 0.05}


def bull_flag_at(df: pd.DataFrame, end: int, p: Dict = FLAG) -> Optional[Dict]:
    first = max(0, end - p["flag_max_bars"])
    if end - p["flag_min_bars"] < first:
        return None
    high = np.log(df["High"].to_numpy()[:end + 1])
    low = np.log(df["Low"].to_numpy()[:end + 1])
    top = first + int(np.argmax(high[first:end - p["flag_min_bars"] + 1]))
    lo0 = max(0, top - p["pole_max_bars"])
    window = low[lo0:top + 1]
    start = lo0 + int(np.flatnonzero(window == window.min())[-1])
    rise = high[top] - low[start]
    if start == top or rise < np.log(1 + p["pole_min_rise"]):
        return None
    flag_low, flag_high = low[top + 1:].min(), high[top:].max()
    if (high[top] - flag_low) > p["max_retrace"] * rise or flag_high - high[top] > np.log(1 + p["max_over_top"]):
        return None
    return {"pole_start": start, "pole_top": top, "end": int(end),
            "pole_low": float(np.exp(low[start])), "pole_high": float(np.exp(high[top])),
            "flag_low": float(np.exp(flag_low)), "flag_high": float(np.exp(flag_high)),
            "flag_high_idx": top + int(np.argmax(high[top:]))}
