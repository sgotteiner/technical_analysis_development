"""
Setup: a bull flag running into a strong resistance (owner, 2026-09-22: buy the breakout of the
resistance, maybe after a retest, "based on this strong resistance that stopped it the previous
time it reached there and the bullish pattern").

Detected at bar `end` (bars <= end only):
  flag        a bull flag ends at `end` (modules/shapes/bull_flag.py)
  resistance  a strong resistance line whose peaks came before the pole started
              (modules/shapes/strong_resistance.py)
  near        the flag's high is within `near` of the line (below or just above it)
  pick        the closest line; then more touches; then the most recent last peak
  broken      the close at `end` is above the line (the breakout has happened)
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from modules.shapes.bull_flag import bull_flag_at, FLAG
from modules.shapes.strong_resistance import resistance_lines, line_value, RESISTANCE
from modules.shapes.sr_turning_points import turning_points

NEAR = 0.03


def setup_at(df: pd.DataFrame, end: int, flag_p: Dict = FLAG, res_p: Dict = RESISTANCE, near: float = NEAR,
             tp: Optional[Dict] = None) -> Optional[Dict]:
    flag = bull_flag_at(df, end, flag_p)
    if flag is None:
        return None
    best, best_key = None, None
    for line in resistance_lines(df, end, flag["pole_start"], res_p, tp):
        gap = float(np.log(flag["flag_high"]) - line_value(line, flag["flag_high_idx"]))
        if abs(gap) > np.log(1 + near):
            continue
        key = (-abs(gap), line["touches"], line["last_peak"])
        if best_key is None or key > best_key:
            best, best_key = (line, gap), key
    if best is None:
        return None
    line, gap = best
    close_now = float(np.log(df["Close"].iloc[end]))
    return {"end": int(end), "flag": flag, "resistance": line, "gap": gap,
            "broken": bool(close_now > line_value(line, end)), "level_now": float(np.exp(line_value(line, end)))}


def scan(df: pd.DataFrame, flag_p: Dict = FLAG, res_p: Dict = RESISTANCE, near: float = NEAR) -> List[Dict]:
    """The setup on every bar where there is one. Turning points are computed once on the whole
    df; each bar uses only points confirmed by it, so this equals a live, bar-by-bar run."""
    tp = turning_points(df, res_p["magnitude"])
    found = (setup_at(df, end, flag_p, res_p, near, tp) for end in range(flag_p["flag_max_bars"], len(df)))
    return [s for s in found if s is not None]


def episodes(found: List[Dict]) -> List[Dict]:
    """Runs of consecutive bars with a setup; each keeps the setup of its last bar."""
    out = []
    for s in found:
        if out and s["end"] == out[-1]["last"] + 1:
            out[-1].update(last=s["end"], days=out[-1]["days"] + 1, setup=s)
        else:
            out.append({"first": s["end"], "last": s["end"], "days": 1, "setup": s})
    return out
