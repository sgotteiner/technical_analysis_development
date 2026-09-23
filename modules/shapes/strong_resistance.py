"""
Strong resistance lines (owner's setup, 2026-09-22: "strong resistance that stopped it the
previous time it reached there"). Uses bars <= end only.

  line        through two major peaks (zigzag of `magnitude`, confirmed by `end`, inside the
              lookback, both before `before` — the bar where the new approach starts)
  resistance  no close above the line by more than break_tol from its first peak to `before`
  strong      after its last peak price fell >= min_rejection (log) before `before`
  touches     major peaks within touch_tol of the line (reported, not required beyond the two)
Thresholds are Claude's (from the owner's BTC example: two peaks ~1.7% apart, a 30% fall after
the last one).
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from modules.shapes.sr_turning_points import turning_points, PEAK

RESISTANCE = {"magnitude": 0.10, "lookback": 400, "break_tol": 0.02, "min_rejection": 0.15, "touch_tol": 0.015}


def resistance_lines(df: pd.DataFrame, end: int, before: int, p: Dict = RESISTANCE,
                     tp: Optional[Dict] = None) -> List[Dict]:
    tp = tp if tp is not None else turning_points(df, p["magnitude"])
    keep = (tp["conf"] <= end) & (tp["kind"] == PEAK) & (tp["idx"] >= end - p["lookback"]) & (tp["idx"] < before)
    x, y = tp["idx"][keep], tp["y"][keep]
    close = np.log(df["Close"].to_numpy()[:end + 1])
    low = np.log(df["Low"].to_numpy()[:end + 1])
    over, need = np.log(1 + p["break_tol"]), np.log(1 + p["min_rejection"])
    out = []
    for b in range(1, len(x)):
        if before <= x[b] + 1:
            continue
        rejection = float(y[b] - low[x[b] + 1:before + 1].min())
        if rejection < need:
            continue
        for a in range(b):
            slope = float((y[b] - y[a]) / (x[b] - x[a]))
            xs = np.arange(x[a], before + 1)
            if (close[xs] > y[a] + slope * (xs - x[a]) + over).any():
                continue
            touches = int((np.abs(y - (y[a] + slope * (x - x[a]))) <= np.log(1 + p["touch_tol"])).sum())
            out.append({"x1": int(x[a]), "y1": float(y[a]), "slope": slope, "last_peak": int(x[b]),
                        "rejection": rejection, "touches": touches})
    return out


def line_value(line: Dict, x) -> float:
    """Log price of the line at bar x."""
    return line["y1"] + line["slope"] * (x - line["x1"])
