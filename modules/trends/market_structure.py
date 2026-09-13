import numpy as np
import pandas as pd
from modules.base import BaseBlock, BlockResult

class MarketStructureBlock(BaseBlock):
    """
    Category 1: Trend Classifier (Institutional Market Structure)
    Identifies Swing Highs (SH) & Swing Lows (SL).
    Classifies Market Regime:
    - Bullish Trend: Higher Highs (HH) + Higher Lows (HL)
    - Bearish Trend: Lower Highs (LH) + Lower Lows (LL)
    - Break of Structure (BOS): Price breaking prior SH/SL
    """
    def __init__(self, tf='1D', pivot_span=5):
        super().__init__(name=f"Market Structure ({tf} HH/HL & BOS)", category="Trend", tf=tf)
        self.pivot_span = pivot_span
        
    def find_pivots(self, high, low):
        n = len(high)
        w = self.pivot_span
        sh = [] # (index, price, 'SH')
        sl = [] # (index, price, 'SL')
        
        for i in range(w, n - w):
            if all(high[i] >= high[i - k] for k in range(1, w + 1)) and \
               all(high[i] >= high[i + k] for k in range(1, w + 1)):
                sh.append((i, high[i]))
            if all(low[i] <= low[i - k] for k in range(1, w + 1)) and \
               all(low[i] <= low[i + k] for k in range(1, w + 1)):
                sl.append((i, low[i]))
        return sh, sl

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        n = len(df)
        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        
        sh, sl = self.find_pivots(high, low)
        mask = np.zeros(n, dtype=bool)
        
        for i in range(20, n):
            c_sh = [p for p in sh if p[0] < i]
            c_sl = [p for p in sl if p[0] < i]
            
            if len(c_sh) >= 2 and len(c_sl) >= 2:
                last_sh2, last_sh1 = c_sh[-2][1], c_sh[-1][1]
                last_sl2, last_sl1 = c_sl[-2][1], c_sl[-1][1]
                
                # Bullish Structure: Higher Highs & Higher Lows OR Bullish BOS
                is_hh_hl = (last_sh1 > last_sh2) and (last_sl1 > last_sl2)
                is_bos = close[i] > last_sh1
                
                if is_hh_hl or is_bos:
                    mask[i] = True
                    
        if self.tf == '1D':
            dates_bullish = set(df.index[mask].strftime('%Y-%m-%d'))
            h1_mask = np.array([df_1h.index[i].strftime('%Y-%m-%d') in dates_bullish for i in range(len(df_1h))])
            return BlockResult(self.name, self.category, self.tf, h1_mask)

        return BlockResult(self.name, self.category, self.tf, mask)
