"""
Where the peaks and valleys come from - the choices the line concepts can switch between
(owner, 2026-10-08: "implementing these concepts with flags will help in testing it").

  zigzag  ours: a % reversal, the size read from the move (modules/shapes/sr_turning_points.py)
  pivots  every pivot script on TradingView: a high higher than `period` bars on each side; known
          `period` bars after it
  atr     the ATR zigzag: a reversal of `mult` average candle ranges, so it widens by itself when
          the market is wild ("the zigzag is too fine after big tops")

All return the turning-point arrays `turning_points` gives (idx, kind, y, conf), so everything
downstream reads them the same way, and `conf` keeps them free of lookahead.
"""
from typing import Dict
import numpy as np
import pandas as pd
from modules.shapes.sr_turning_points import PEAK, VALLEY, turning_points

PIVOT_PERIOD = 10          # the TradingView scripts' default
ATR_LENGTH = 14            # Wilder's
ATR_MULT = 2.5             # "2.0-2.5 balanced, good for swing trading" - the ATR ZigZag script's default


def pivot_points(df: pd.DataFrame, period: int = PIVOT_PERIOD) -> Dict[str, np.ndarray]:
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    rows = []
    for i in range(period, len(df) - period):
        win = slice(i - period, i + period + 1)
        if high[i] == high[win].max():
            rows.append((i, PEAK, float(np.log(high[i])), i + period))
        if low[i] == low[win].min():
            rows.append((i, VALLEY, float(np.log(low[i])), i + period))
    cols = list(zip(*rows)) if rows else [[], [], [], []]
    return {"idx": np.array(cols[0], dtype=int), "kind": np.array(cols[1], dtype=int),
            "y": np.array(cols[2], dtype=float), "conf": np.array(cols[3], dtype=int)}


def atr_pct(df: pd.DataFrame, length: int = ATR_LENGTH) -> np.ndarray:
    """Wilder's average true range, as a share of the close."""
    high, low, close = df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy()
    prev = np.concatenate([[close[0]], close[:-1]])
    tr = np.maximum(high - low, np.maximum(abs(high - prev), abs(low - prev)))
    atr = pd.Series(tr).ewm(alpha=1 / length, adjust=False).mean().to_numpy()
    return atr / close


def atr_zigzag(df: pd.DataFrame, mult: float = ATR_MULT) -> Dict[str, np.ndarray]:
    return turning_points(df, mult * atr_pct(df))


def swing_points(df: pd.DataFrame, source: str, size: float, cache: Dict) -> Dict[str, np.ndarray]:
    """The whole history's points from `source`, cached per source and setting."""
    key = ("swings", source, size if source == "zigzag" else None)
    if key not in cache:
        cache[key] = (turning_points(df, size) if source == "zigzag"
                      else pivot_points(df) if source == "pivots" else atr_zigzag(df))
    return cache[key]
