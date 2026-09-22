import pandas as pd
import numpy as np
from ta.trend import sma_indicator
from modules.base import BaseBlock, BlockResult

class SmaTrendBlock(BaseBlock):
    """
    Category 1: Trend Classifier (SMA Trend)
    """
    def __init__(self, tf='1D', period=200):
        super().__init__(name=f"SMA ({tf} {period})", category="Trend", tf=tf)
        self.period = period
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        sma = sma_indicator(df['Close'], window=self.period).fillna(0).values
        close = df['Close'].values
        
        mask = (sma > 0) & (close > sma)
        # Native-timeframe mask; alignment is owned by the strategy orchestrator.
        return BlockResult(self.name, self.category, self.tf, mask)
