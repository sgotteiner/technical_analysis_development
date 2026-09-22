"""
Descriptive metrics for a market period (daily OHLC): how much, how long, how clean,
how rough. All returns are on daily closes; volatility is annualised with 365 days.
"""
from typing import Dict
import numpy as np
import pandas as pd

DAYS_PER_YEAR = 365
EPISODE_THRESHOLD = 0.10   # a pullback/bounce counts once it exceeds 10%
STEP_DAYS = 21             # a flat "step" lasts at least this many days...
STEP_BAND = 1.15           # ...with its highest close <= 1.15 x its lowest close
TOUCH_ZONE = 0.20          # top / bottom 20% of the period's close range


def flat_steps(close: np.ndarray, days: int = STEP_DAYS, band: float = STEP_BAND) -> int:
    """Non-overlapping stretches of `days` bars whose closes stay within `band` (max/min)."""
    count, i = 0, 0
    while i + days <= len(close):
        w = close[i:i + days]
        if w.max() / w.min() <= band:
            count, i = count + 1, i + days
        else:
            i += 1
    return count


def range_touches(close: np.ndarray, zone: float = TOUCH_ZONE) -> int:
    """Alternating visits to the top and bottom `zone` of the close range (T,B,T,B -> 4)."""
    lo, hi = close.min(), close.max()
    top, bottom = hi - (hi - lo) * zone, lo + (hi - lo) * zone
    last, count = None, 0
    for c in close:
        z = "top" if c >= top else "bottom" if c <= bottom else None
        if z and z != last:
            last, count = z, count + 1
    return count


def _max_drawdown(close: np.ndarray) -> float:
    """Deepest drop from a running high, as a positive fraction."""
    peak = np.maximum.accumulate(close)
    return float(np.max(1 - close / peak))


def _max_runup(close: np.ndarray) -> float:
    """Biggest rise from a running low, as a positive fraction."""
    trough = np.minimum.accumulate(close)
    return float(np.max(close / trough - 1))


def _count_drawdowns(close: np.ndarray, threshold: float) -> int:
    """Distinct drops of more than `threshold` from a running high (an episode ends at a new high)."""
    count, peak, in_episode = 0, close[0], False
    for c in close[1:]:
        if c >= peak:
            peak, in_episode = c, False
        elif not in_episode and 1 - c / peak > threshold:
            count, in_episode = count + 1, True
    return count


def _r2(y: np.ndarray) -> float:
    """R^2 of a straight-line fit to y over time; 0 for a flat series."""
    if np.ptp(y) == 0:
        return 0.0
    return float(np.corrcoef(np.arange(len(y)), y)[0, 1] ** 2)


def _true_range_pct(df: pd.DataFrame) -> float:
    prev = df["Close"].shift()
    tr = pd.concat([df["High"] - df["Low"], (df["High"] - prev).abs(), (df["Low"] - prev).abs()], axis=1).max(axis=1)
    return float((tr / prev).iloc[1:].mean())


def period_metrics(df: pd.DataFrame) -> Dict[str, float]:
    """Metrics for one period. `df` holds only the period's daily bars (Open/High/Low/Close)."""
    close = df["Close"].to_numpy(dtype=float)
    logret = np.diff(np.log(close))
    days = (df.index[-1] - df.index[0]).days          # elapsed days, not bar count
    total = close[-1] / close[0] - 1
    path, std = np.abs(logret).sum(), logret.std()
    return {
        "return": float(total),
        "days": days,
        "per_month": float((1 + total) ** (30 / days) - 1),
        "efficiency": float(abs(logret.sum()) / path) if path else 0.0,
        "r2": _r2(np.log(close)),
        "up_days": float(np.mean(logret > 0)),
        "trend_noise": float(logret.mean() / std * np.sqrt(DAYS_PER_YEAR)) if std else 0.0,
        "volatility": float(logret.std() * np.sqrt(DAYS_PER_YEAR)),
        "atr_pct": _true_range_pct(df),
        "max_pullback": _max_drawdown(close),
        "max_bounce": _max_runup(close),
        "pullbacks_10": _count_drawdowns(close, EPISODE_THRESHOLD),
        "bounces_10": _count_drawdowns(1 / close, EPISODE_THRESHOLD),
        "band": float(close.max() / close.min()),
        "steps": flat_steps(close),
        "touches": range_touches(close),
        "best_day": float(np.exp(logret.max()) - 1),
        "worst_day": float(np.exp(logret.min()) - 1),
    }
