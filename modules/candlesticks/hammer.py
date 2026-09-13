import numpy as np
import pandas as pd
from modules.base import BaseBlock, BlockResult

class HammerBlock(BaseBlock):
    """
    Category 3: Candlestick Pattern (Hammer Reversal)
    """
    def __init__(self, tf='1H'):
        super().__init__(name=f"Hammer ({tf})", category="Candlestick", tf=tf)
        
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
            body_curr = abs(c[i] - o[i])
            range_curr = h[i] - l[i]
            lower_wick = min(o[i], c[i]) - l[i]
            upper_wick = h[i] - max(o[i], c[i])
            
            if (range_curr > 0) and (body_curr > 0) and (lower_wick >= 2 * body_curr) and (upper_wick <= 0.5 * body_curr):
                mask[i] = True
                visual_data[i] = {
                    'start_idx': i,
                    'end_idx': i,
                    'high': h[i],
                    'low': l[i],
                    'name': 'Hammer Reversal'
                }
                
        return BlockResult(self.name, self.category, self.tf, mask, visual_data=visual_data)
