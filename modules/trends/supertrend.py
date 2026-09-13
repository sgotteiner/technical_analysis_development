import numpy as np
import pandas as pd
from ta.volatility import average_true_range
from modules.base import BaseBlock, BlockResult

class SuperTrendBlock(BaseBlock):
    """
    Category 1: Trend Classifier (ATR SuperTrend)
    Calculates the dynamic SuperTrend support/resistance line.
    """
    def __init__(self, tf='1D', period=10, multiplier=3.0):
        super().__init__(name=f"SuperTrend ({tf} {period},{multiplier})", category="Trend", tf=tf)
        self.period = period
        self.multiplier = multiplier
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        high = df['High'].values
        low = df['Low'].values
        close = df['Close'].values
        n = len(df)
        
        atr = average_true_range(df['High'], df['Low'], df['Close'], window=self.period).fillna(0).values
        
        basic_upper = (high + low) / 2.0 + self.multiplier * atr
        basic_lower = (high + low) / 2.0 - self.multiplier * atr
        
        final_upper = np.zeros(n)
        final_lower = np.zeros(n)
        trend = np.ones(n, dtype=int)
        
        for i in range(1, n):
            # Lower Band
            if basic_lower[i] > final_lower[i-1] or close[i-1] < final_lower[i-1]:
                final_lower[i] = basic_lower[i]
            else:
                final_lower[i] = final_lower[i-1]
                
            # Upper Band
            if basic_upper[i] < final_upper[i-1] or close[i-1] > final_upper[i-1]:
                final_upper[i] = basic_upper[i]
            else:
                final_upper[i] = final_upper[i-1]
                
            # Trend Direction
            if trend[i-1] == 1:
                if close[i] < final_lower[i]:
                    trend[i] = -1
                else:
                    trend[i] = 1
            else:
                if close[i] > final_upper[i]:
                    trend[i] = 1
                else:
                    trend[i] = -1
                    
        mask = trend == 1
        
        if self.tf == '1D':
            dates_bullish = set(df.index[mask].strftime('%Y-%m-%d'))
            h1_mask = np.array([df_1h.index[i].strftime('%Y-%m-%d') in dates_bullish for i in range(len(df_1h))])
            return BlockResult(self.name, self.category, self.tf, h1_mask)
            
        return BlockResult(self.name, self.category, self.tf, mask)
