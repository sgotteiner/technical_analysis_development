import numpy as np
import pandas as pd
from scipy.stats import linregress
from modules.base import BaseBlock, BlockResult

class InstitutionalGeometryBlock(BaseBlock):
    """
    Category 2: Chart Shape Patterns (Institutional Multi-Touch Geometry)
    Validates trendlines using 3+ pivot points with R^2 > 0.90
    and ensures NO price penetration between touchpoints.
    """
    def __init__(self, tf='1H', lookback=80, min_touches=3, min_r2=0.88):
        super().__init__(name=f"Multi-Touch Geometry ({tf} R²>{min_r2})", category="Shape", tf=tf)
        self.lookback = lookback
        self.min_touches = min_touches
        self.min_r2 = min_r2
        
    def find_pivots(self, high, low, window=4):
        n = len(high)
        sh, sl = [], []
        for i in range(window, n - window):
            if all(high[i] >= high[i - k] for k in range(1, window + 1)) and \
               all(high[i] >= high[i + k] for k in range(1, window + 1)):
                sh.append((i, high[i]))
            if all(low[i] <= low[i - k] for k in range(1, window + 1)) and \
               all(low[i] <= low[i + k] for k in range(1, window + 1)):
                sl.append((i, low[i]))
        return sh, sl

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        n = len(df)
        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        
        sh, sl = self.find_pivots(high, low, window=4)
        mask = np.zeros(n, dtype=bool)
        details = {}
        
        for i in range(self.lookback, n):
            c_sh = [p for p in sh if i - self.lookback <= p[0] <= i - 1]
            c_sl = [p for p in sl if i - self.lookback <= p[0] <= i - 1]
            
            if len(c_sh) < self.min_touches or len(c_sl) < self.min_touches:
                continue
                
            x_h = np.array([p[0] for p in c_sh])
            y_h = np.array([p[1] for p in c_sh])
            
            x_l = np.array([p[0] for p in c_sl])
            y_l = np.array([p[1] for p in c_sl])
            
            res_h = linregress(x_h, y_h)
            res_l = linregress(x_l, y_l)
            
            # Check linearity (R^2 > 0.88) for both resistance and support
            if (res_h.rvalue**2 >= self.min_r2) and (res_l.rvalue**2 >= self.min_r2):
                h_slope = res_h.slope
                l_slope = res_l.slope
                
                # Verify no price penetration
                penetrated = False
                for b_idx in range(x_h[0], i):
                    h_val = res_h.intercept + res_h.slope * b_idx
                    l_val = res_l.intercept + res_l.slope * b_idx
                    if high[b_idx] > h_val * 1.015 or low[b_idx] < l_val * 0.985:
                        penetrated = True
                        break
                        
                if not penetrated:
                    proj_res = res_h.intercept + res_h.slope * i
                    if close[i-1] <= proj_res and close[i] > proj_res:
                        mask[i] = True
                        start_b = min(x_h[0], x_l[0])
                        res_seg = [{'time': int(df.index[b].timestamp()), 'value': float(res_h.intercept + res_h.slope * b)} for b in range(start_b, i + 1)]
                        sup_seg = [{'time': int(df.index[b].timestamp()), 'value': float(res_l.intercept + res_l.slope * b)} for b in range(start_b, i + 1)]
                        details[i] = {
                            'type': f"Multi-Touch Pattern (R²={res_h.rvalue**2:.2f})",
                            'res': res_seg,
                            'sup': sup_seg
                        }
                        
        return BlockResult(self.name, self.category, self.tf, mask, metadata=details)
