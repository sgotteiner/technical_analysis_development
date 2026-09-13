"""
Timestamp & Timeframe Alignment Helpers.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any

def map_daily_signals_to_intraday(
    df_daily: pd.DataFrame,
    df_intraday: pd.DataFrame,
    daily_mask: pd.Series
) -> np.ndarray:
    """
    Map daily boolean signals/regime mask to intraday dataframe (1H or 5M)
    by date formatting (%Y-%m-%d).
    """
    if df_daily.empty or df_intraday.empty:
        return np.zeros(len(df_intraday), dtype=bool)

    daily_signal_dict = dict(zip(df_daily.index.strftime('%Y-%m-%d'), daily_mask))
    intraday_mask = np.array([
        daily_signal_dict.get(df_intraday.index[i].strftime('%Y-%m-%d'), False)
        for i in range(len(df_intraday))
    ])
    return intraday_mask

def map_hourly_signals_to_5m(
    df_1h: pd.DataFrame,
    df_5m: pd.DataFrame,
    h1_mask: pd.Series
) -> np.ndarray:
    """
    Map 1H boolean signals to 5M dataframe by timestamp bucket (%Y-%m-%d %H:00).
    """
    if df_1h.empty or df_5m.empty:
        return np.zeros(len(df_5m), dtype=bool)

    h1_signal_dict = dict(zip(df_1h.index.strftime('%Y-%m-%d %H:00'), h1_mask))
    m5_mask = np.array([
        h1_signal_dict.get(df_5m.index[i].strftime('%Y-%m-%d %H:00'), False)
        for i in range(len(df_5m))
    ])
    return m5_mask
