import pandas as pd
import numpy as np
from modules.base import BaseBlock, BlockResult

class MacdTrendBlock(BaseBlock):
    """
    Category 1: Trend Classifier (MACD Regime)
    """
    def __init__(self, tf='1D', fast=12, slow=26, signal=9):
        super().__init__(name=f"MACD Regime ({tf})", category="Trend", tf=tf)
        self.fast = fast
        self.slow = slow
        self.signal = signal
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        close = df['Close']
        
        fast_ema = close.ewm(span=self.fast, adjust=False).mean()
        slow_ema = close.ewm(span=self.slow, adjust=False).mean()
        macd = fast_ema - slow_ema
        sig = macd.ewm(span=self.signal, adjust=False).mean()
        
        mask = (macd > sig) & (macd > 0)
        # Native-timeframe mask; alignment is owned by the strategy orchestrator.
        return BlockResult(self.name, self.category, self.tf, mask.values)
