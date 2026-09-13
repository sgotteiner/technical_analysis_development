import numpy as np
import pandas as pd
from modules.base import BaseBlock, BlockResult

class TrianglePatternBlock(BaseBlock):
    """
    Category 2: Chart Shape Patterns (Triangles)
    """
    def __init__(self, tf='1H', pivot_window=3, lookback=60):
        super().__init__(name=f"Triangles ({tf})", category="Shape", tf=tf)
        self.pivot_window = pivot_window
        self.lookback = lookback
        
    def find_pivots(self, df):
        highs = df['High'].values
        lows = df['Low'].values
        n = len(df)
        w = self.pivot_window
        phs, pls = [], []
        for i in range(w, n - w):
            if all(highs[i] > highs[i - k] for k in range(1, w + 1)) and \
               all(highs[i] >= highs[i + k] for k in range(1, w + 1)):
                phs.append((i, highs[i]))
            if all(lows[i] < lows[i - k] for k in range(1, w + 1)) and \
               all(lows[i] <= lows[i + k] for k in range(1, w + 1)):
                pls.append((i, lows[i]))
        return phs, pls

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        phs, pls = self.find_pivots(df)
        n = len(df)
        mask = np.zeros(n, dtype=bool)
        details = {}
        
        for i in range(self.lookback, n):
            c_phs = [p for p in phs if i - self.lookback <= p[0] <= i - 1]
            c_pls = [p for p in pls if i - self.lookback <= p[0] <= i - 1]
            if len(c_phs) < 2 or len(c_pls) < 2: continue
            
            h1_idx, h1_val = c_phs[-2]
            h2_idx, h2_val = c_phs[-1]
            l1_idx, l1_val = c_pls[-2]
            l2_idx, l2_val = c_pls[-1]
            
            h_slope = (h2_val - h1_val) / (h2_idx - h1_idx)
            l_slope = (l2_val - l1_val) / (l2_idx - l1_idx)
            
            if (h_slope <= 0) and (l_slope > 0):
                proj_res = h2_val + h_slope * (i - h2_idx)
                if df['Close'].iloc[i-1] <= proj_res and df['Close'].iloc[i] > proj_res:
                    mask[i] = True
                    start_b = min(h1_idx, l1_idx)
                    res_seg = [{'time': int(df.index[b].timestamp()), 'value': float(h1_val + h_slope * (b - h1_idx))} for b in range(start_b, i + 1)]
                    sup_seg = [{'time': int(df.index[b].timestamp()), 'value': float(l1_val + l_slope * (b - l1_idx))} for b in range(start_b, i + 1)]
                    details[i] = {'type': 'Triangle', 'res': res_seg, 'sup': sup_seg}
                    
        return BlockResult(self.name, self.category, self.tf, mask, metadata=details)
