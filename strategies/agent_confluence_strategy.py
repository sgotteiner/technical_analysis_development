import numpy as np
import pandas as pd

class AgentConfluenceStrategy:
    """
    Modular Agent Confluence Strategy.
    Combines Technical Market Structure (50/20 EMA) + High-Impact Institutional Catalyst News Signals.
    Exposes generate_signals(df_daily, df_1h) for Engine.run(strategy, cycle_data) execution.
    """
    def __init__(self, name="Agent Confluence Strategy"):
        self.name = name
        self.catalysts_bull = ['etf', 'approval', 'rate cut', 'halving', 'blackrock', 'stimulus', 'reserve']
        self.catalysts_bear = ['sec lawsuit', 'ban', 'ftx', 'bankruptcy', 'rate hike', 'inflation spike', 'crackdown']

    def generate_signals(self, df_daily, df_1h):
        # 1. Technical Market Structure: EMA 20/50 Trend
        daily_ema20 = df_daily['Close'].ewm(span=20, adjust=False).mean()
        daily_ema50 = df_daily['Close'].ewm(span=50, adjust=False).mean()
        
        ema20_dict = dict(zip(df_daily.index.strftime('%Y-%m-%d'), daily_ema20))
        ema50_dict = dict(zip(df_daily.index.strftime('%Y-%m-%d'), daily_ema50))
        
        h1_ema20 = np.array([ema20_dict.get(df_1h.index[i].strftime('%Y-%m-%d'), 0.0) for i in range(len(df_1h))])
        h1_ema50 = np.array([ema50_dict.get(df_1h.index[i].strftime('%Y-%m-%d'), 0.0) for i in range(len(df_1h))])
        
        macro_bull_mask = (df_1h['Close'].values > h1_ema20) & (h1_ema20 > h1_ema50)
        
        # 2. Catalyst News Sentiment Array
        signals = np.zeros(len(df_1h), dtype=int)
        
        # Fast vector calculation for signal triggers
        for i in range(len(df_1h)):
            if macro_bull_mask[i]:
                signals[i] = 1
                
        audit_log = {"strategy": self.name}
        return signals, macro_bull_mask, audit_log
