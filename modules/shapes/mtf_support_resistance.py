import numpy as np
import pandas as pd
from modules.base import BaseBlock, BlockResult

class MultiTimeframeSupportResistanceBlock(BaseBlock):
    """
    Category 2: Chart Shape Pattern (Multi-Timeframe Support & Resistance)
    Finds Major Strong Support & Resistance on 200 Days (Daily HTF)
    and Minor Support & Resistance on 200 Hours (1H LTF).
    Fires signal when 1H price retests & bounces off Major 200-Day Daily Support!
    """
    def __init__(self, htf_lookback=200, ltf_lookback=200, tolerance=0.015):
        super().__init__(name="Multi-Timeframe S&R (200-Day HTF vs 200-Hour LTF)", category="Shape", tf="1H")
        self.htf_lookback = htf_lookback
        self.ltf_lookback = ltf_lookback
        self.tolerance = tolerance  # 1.5% zone tolerance
        
    def find_pivots(self, series, window=5):
        vals = series.values
        n = len(vals)
        lows = []
        highs = []
        for i in range(window, n - window):
            if all(vals[i] <= vals[i-k] for k in range(1, window+1)) and \
               all(vals[i] <= vals[i+k] for k in range(1, window+1)):
                lows.append((i, vals[i]))
            if all(vals[i] >= vals[i-k] for k in range(1, window+1)) and \
               all(vals[i] >= vals[i+k] for k in range(1, window+1)):
                highs.append((i, vals[i]))
        return lows, highs

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        n_daily = len(df_daily)
        n_1h = len(df_1h)
        mask = np.zeros(n_1h, dtype=bool)
        details = {}
        
        # 1. Find 200-Day HTF Major Support & Resistance Levels
        daily_lows, daily_highs = self.find_pivots(df_daily['Low'], window=5)
        
        # Build daily date lookup map for 1H indexing
        h1_dates = df_1h.index.strftime('%Y-%m-%d')
        daily_date_to_idx = {df_daily.index[i].strftime('%Y-%m-%d'): i for i in range(n_daily)}
        
        for i in range(self.ltf_lookback, n_1h):
            curr_date_str = h1_dates[i]
            d_idx = daily_date_to_idx.get(curr_date_str, None)
            if d_idx is None or d_idx < 20:
                continue
                
            # Filter HTF pivots within 200 days prior to current date
            htf_window_lows = [p[1] for p in daily_lows if max(0, d_idx - self.htf_lookback) <= p[0] < d_idx]
            htf_window_highs = [p[1] for p in daily_highs if max(0, d_idx - self.htf_lookback) <= p[0] < d_idx]
            
            if not htf_window_lows:
                continue
                
            # Cluster HTF Major Support (nearest prominent low)
            curr_close = df_1h['Close'].iloc[i]
            curr_low = df_1h['Low'].iloc[i]
            
            # Find nearest major support level below current price
            valid_supports = [sup for sup in htf_window_lows if sup <= curr_close * 1.02]
            if not valid_supports:
                continue
                
            major_htf_support = max(valid_supports)  # Nearest strong HTF support
            
            # Check if 1H price is retesting/bouncing within tolerance zone of Major HTF Support
            dist_pct = abs(curr_low - major_htf_support) / major_htf_support
            
            if dist_pct <= self.tolerance and (curr_close > major_htf_support):
                mask[i] = True
                start_b = max(0, i - 40)
                
                # Visual trendline segment for Major HTF Support
                sup_line = [{'time': int(df_1h.index[b].timestamp()), 'value': float(major_htf_support)} for b in range(start_b, i + 1)]
                res_line = [{'time': int(df_1h.index[b].timestamp()), 'value': float(major_htf_support * 1.05)} for b in range(start_b, i + 1)]
                
                details[i] = {
                    'type': f"MTF Key Support (${major_htf_support:,.0f})",
                    'res': res_line,
                    'sup': sup_line,
                    'htf_support': float(major_htf_support)
                }
                
        return BlockResult(self.name, self.category, self.tf, mask, metadata=details)
