"""
Flags, decided on the first close out of the flag the way the pole ran (Edwards & Magee). The flag
itself is the existing detector (modules/shapes/bull_flag.py, read from his first drawn flag); a
bear flag is the same detector on the chart turned upside down, so both sides share one rule.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from modules.shapes.bull_flag import bull_flag_at


def mirrored(df: pd.DataFrame) -> pd.DataFrame:
    """The chart upside down: a fall becomes a rise of the same size (in log price)."""
    return pd.DataFrame({"Open": 1 / df["Open"], "High": 1 / df["Low"], "Low": 1 / df["High"],
                         "Close": 1 / df["Close"]}, index=df.index)


def flag(df: pd.DataFrame, d: int, bull: bool, flipped: Optional[pd.DataFrame] = None) -> Optional[Dict]:
    """A flag that stood yesterday and today's close left it the pole's way."""
    src = df if bull else (flipped if flipped is not None else mirrored(df))
    f = bull_flag_at(src, d - 1)
    if f is None or not src["Close"].iloc[d] > f["flag_high"]:
        return None
    back = (lambda x: x) if bull else (lambda x: 1 / x)
    top, start = back(f["pole_high"]), back(f["pole_low"])
    edge = back(f["flag_high"])
    pole = abs(np.log(top / start))
    return {"type": "bull_flag" if bull else "bear_flag", "direction": "up" if bull else "down",
            "bar": d, "points": [(f["pole_start"], start), (f["pole_top"], top)],
            "neckline": {"kind": "level", "price": float(edge), "low": float(edge), "high": float(edge)},
            "target": float(edge * np.exp(pole if bull else -pole))}
