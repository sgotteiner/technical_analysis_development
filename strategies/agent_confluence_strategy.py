import numpy as np
from strategies.base_strategy import BaseStrategy


class AgentConfluenceStrategy(BaseStrategy):
    """
    Modular Agent Confluence Strategy.
    Technical Market Structure (20/50 EMA) computed on daily candles, connected
    onto the 1H trading timeframe via the no-lookahead aligner (BaseStrategy.align).
    """
    def __init__(self, name="Agent Confluence Strategy"):
        super().__init__(name)
        self.catalysts_bull = ['etf', 'approval', 'rate cut', 'halving', 'blackrock', 'stimulus', 'reserve']
        self.catalysts_bear = ['sec lawsuit', 'ban', 'ftx', 'bankruptcy', 'rate hike', 'inflation spike', 'crackdown']

    def generate_signals(self, df_daily, df_1h):
        # Daily EMA structure (computed on completed daily candles)
        daily_ema20 = df_daily['Close'].ewm(span=20, adjust=False).mean()
        daily_ema50 = df_daily['Close'].ewm(span=50, adjust=False).mean()

        # Connect daily EMAs onto 1H bars with NO lookahead.
        h1_ema20 = self.align(df_daily, df_1h, daily_ema20, fill_value=0.0)
        h1_ema50 = self.align(df_daily, df_1h, daily_ema50, fill_value=0.0)

        macro_bull_mask = (df_1h['Close'].values > h1_ema20) & (h1_ema20 > h1_ema50)
        signals = macro_bull_mask.astype(int)

        audit_log = {"strategy": self.name}
        return signals, macro_bull_mask, audit_log
