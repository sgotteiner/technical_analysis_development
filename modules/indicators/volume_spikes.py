import numpy as np
import pandas as pd
from ta.trend import sma_indicator
from modules.base import BaseBlock, BlockResult

class VolumeSpikeBlock(BaseBlock):
    """
    Category 4: Price & Volume Indicator (Volume Spike)
    """
    def __init__(self, tf='1H', ratio=1.15, period=20):
        super().__init__(name=f"Volume Spike ({tf} > {ratio}x {period}SMA)", category="Indicator", tf=tf)
        self.period = int(period)
        self.ratio = float(ratio)
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        vol_sma = sma_indicator(df['Volume'], window=self.period).fillna(0).values
        vol_curr = df['Volume'].values
        
        mask = (vol_sma > 0) & (vol_curr >= self.ratio * vol_sma)
        return BlockResult(self.name, self.category, self.tf, mask)
