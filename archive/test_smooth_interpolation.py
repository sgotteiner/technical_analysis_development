import sys
import os
import pandas as pd
import numpy as np
import ta

sys.path.append('.')
from modules.data.data_container import CYCLE_2

df_1h = CYCLE_2.df_1h.copy()
df_daily = CYCLE_2.df_daily.copy()

# Daily Indicators
daily_ema20 = ta.trend.ema_indicator(df_daily['Close'], window=20)
daily_ema50 = ta.trend.ema_indicator(df_daily['Close'], window=50)
daily_sma200 = ta.trend.sma_indicator(df_daily['Close'], window=200)
daily_rsi = ta.momentum.rsi(df_daily['Close'], window=14)
daily_adx = ta.trend.adx(df_daily['High'], df_daily['Low'], df_daily['Close'], window=14)

# Resample Daily series to 1H index and linearly interpolate to remove stair-stepping
def create_smooth_1h_series(daily_series, h1_index):
    # Reindex daily series to hourly timestamps, then interpolate linearly
    s_h1 = daily_series.reindex(daily_series.index.union(h1_index)).sort_index()
    s_h1_interp = s_h1.interpolate(method='time').reindex(h1_index)
    return s_h1_interp.ffill().bfill()

smooth_ema20 = create_smooth_1h_series(daily_ema20, df_1h.index)
smooth_ema50 = create_smooth_1h_series(daily_ema50, df_1h.index)
smooth_sma200 = create_smooth_1h_series(daily_sma200, df_1h.index)
smooth_rsi = create_smooth_1h_series(daily_rsi, df_1h.index)
smooth_adx = create_smooth_1h_series(daily_adx, df_1h.index)

print("Smooth 1H Series created successfully!")
print("Sample smooth RSI first 5 values:", smooth_rsi.iloc[100:105].values)
