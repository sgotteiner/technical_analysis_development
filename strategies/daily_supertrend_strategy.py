import numpy as np
import ta.trend
import ta.momentum
from strategies.base_strategy import BaseStrategy


class DailySupertrendStrategy(BaseStrategy):
    """
    Daily Multi-Day Swing Strategy designed to capture multi-week bull runs.
    Computes its regime on Daily candles, then connects it onto the 1H trading
    timeframe via the no-lookahead aligner (BaseStrategy.align).
    """
    def __init__(self, name="Daily Swing Supertrend Strategy", params=None):
        super().__init__(name)
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

        # Daily indicators
        ema_fast_d = ta.trend.ema_indicator(close_d, window=self.params['ema_fast']).fillna(close_d)
        ema_slow_d = ta.trend.ema_indicator(close_d, window=self.params['ema_slow']).fillna(close_d)
        adx_d = ta.trend.adx(high_d, low_d, close_d, window=14).fillna(0.0)
        rsi_d = ta.momentum.rsi(close_d, window=14).fillna(50.0)

        # Daily regime mask (computed on completed daily candles)
        daily_bull_mask = (close_d > ema_fast_d) & (ema_fast_d > ema_slow_d) & \
            (adx_d > self.params['adx_thresh']) & (rsi_d > self.params['rsi_thresh'])

        # Connect the daily regime onto 1H bars with NO lookahead.
        h1_macro_bull = self.align(df_daily, df_1h, daily_bull_mask, fill_value=False)

        signals = np.zeros(len(df_1h), dtype=int)
        signals[h1_macro_bull] = 1

        audit = {"params": self.params}
        return signals, h1_macro_bull, audit
