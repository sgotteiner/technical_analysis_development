"""
Technical Indicator Helper Functions.
"""
import pandas as pd
import ta.trend
import ta.momentum

def compute_ema(series: pd.Series, window: int) -> pd.Series:
    """Compute Exponential Moving Average (EMA)."""
    return ta.trend.ema_indicator(series, window=window).fillna(series)

def compute_adx(high: pd.Series, low: pd.Series, close: pd.Series, window: int = 14) -> pd.Series:
    """Compute Average Directional Index (ADX)."""
    return ta.trend.adx(high, low, close, window=window).fillna(0.0)

def compute_rsi(close: pd.Series, window: int = 14) -> pd.Series:
    """Compute Relative Strength Index (RSI)."""
    return ta.momentum.rsi(close, window=window).fillna(50.0)
