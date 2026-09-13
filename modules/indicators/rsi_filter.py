import numpy as np
import pandas as pd
from ta.momentum import rsi
from modules.base import BaseBlock, BlockResult

class RsiFilterBlock(BaseBlock):
    """
    Category 4: Price & Volume Indicator (RSI Threshold)
    """
    def __init__(self, tf='1H', period=14, max_rsi=72):
        super().__init__(name=f"RSI Filter ({tf} < {max_rsi})", category="Indicator", tf=tf)
        self.period = period
        self.max_rsi = max_rsi
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        rsi_val = rsi(df['Close'], window=self.period).fillna(50).values
        mask = rsi_val < self.max_rsi
        return BlockResult(self.name, self.category, self.tf, mask)
