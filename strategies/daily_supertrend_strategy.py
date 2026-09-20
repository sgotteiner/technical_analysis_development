import numpy as np
import pandas as pd
import ta.trend
import ta.momentum

class DailySupertrendStrategy:
    """
    Daily Multi-Day Swing Strategy designed to capture multi-week bull runs.
    Operates on Daily candles (df_daily) to eliminate 4-hour intraday noise.
    """
    def __init__(self, name="Daily Swing Supertrend Strategy", params=None):
        self.name = name
        self.exit_on_ema50 = False
        self.params = params or {
            'ema_fast': 20,
            'ema_slow': 50,
            'adx_thresh': 20.0,
            'rsi_thresh': 50.0,
            'position_size': 1.5,
            'stop_loss_pct': 0.10
        }

    def generate_signals(self, df_daily, df_1h):
        close_d = df_daily['Close']
        high_d = df_daily['High'] if 'High' in df_daily.columns else close_d
        low_d = df_daily['Low'] if 'Low' in df_daily.columns else close_d
        
        # Daily Indicators
        ema_fast_d = ta.trend.ema_indicator(close_d, window=self.params['ema_fast']).fillna(close_d)
        ema_slow_d = ta.trend.ema_indicator(close_d, window=self.params['ema_slow']).fillna(close_d)
        adx_d = ta.trend.adx(high_d, low_d, close_d, window=14).fillna(0.0)
        rsi_d = ta.momentum.rsi(close_d, window=14).fillna(50.0)
        
        # Daily Bull Mask
        daily_bull_mask = (close_d > ema_fast_d) & (ema_fast_d > ema_slow_d) & (adx_d > self.params['adx_thresh']) & (rsi_d > self.params['rsi_thresh'])

        # Shift by 1 day to eliminate same-day lookahead: day D trades on day D-1's
        # completed daily candle (the close/EMA/ADX/RSI are only known at end of day).
        daily_bull_mask = daily_bull_mask.shift(1, fill_value=False)

        # Map Daily Signals to 1H dataframe timestamps using vectorized strftime
        daily_signal_dict = dict(zip(df_daily.index.strftime('%Y-%m-%d'), daily_bull_mask))
        dates_1h = df_1h.index.strftime('%Y-%m-%d')
        h1_macro_bull = np.array([daily_signal_dict.get(d, False) for d in dates_1h])
        
        signals = np.zeros(len(df_1h), dtype=int)
        signals[h1_macro_bull] = 1
        
        audit = {"params": self.params}
        return signals, h1_macro_bull, audit
