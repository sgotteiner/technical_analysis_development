import numpy as np
import pandas as pd
from modules.base import BaseBlock, BlockResult

class EngulfingBlock(BaseBlock):
    """
    Category 3: Candlestick Pattern (Bullish Engulfing)
    """
    def __init__(self, tf='1H'):
        super().__init__(name=f"Bullish Engulfing ({tf})", category="Candlestick", tf=tf)
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        o = df['Open'].values
        h = df['High'].values
        l = df['Low'].values
        c = df['Close'].values
        n = len(df)
        mask = np.zeros(n, dtype=bool)
        visual_data = {}
        
        for i in range(1, n):
            if (c[i-1] < o[i-1]) and (c[i] > o[i]) and (c[i] >= o[i-1]) and (o[i] <= c[i-1]):
                mask[i] = True
                visual_data[i] = {
                    'start_idx': i - 1,
                    'end_idx': i,
                    'high': max(h[i-1], h[i]),
                    'low': min(l[i-1], l[i]),
                    'name': 'Bullish Engulfing'
                }
                
        return BlockResult(self.name, self.category, self.tf, mask, visual_data=visual_data)
