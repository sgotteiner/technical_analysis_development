import numpy as np
import pandas as pd
from ta.volatility import bollinger_hband, bollinger_lband, keltner_channel_hband, keltner_channel_lband
from modules.base import BaseBlock, BlockResult

class VolatilitySqueezeBlock(BaseBlock):
    """
    Category 4: Price & Volume Indicator (TTM Volatility Squeeze)
    Detects when Bollinger Bands contract inside Keltner Channels and then expand outward.
    """
    def __init__(self, tf='1H', bb_window=20, bb_std=2.0, kc_window=20, kc_mult=1.5):
        super().__init__(name=f"TTM Volatility Squeeze ({tf})", category="Indicator", tf=tf)
        self.bb_window = bb_window
        self.bb_std = bb_std
        self.kc_window = kc_window
        self.kc_mult = kc_mult
        
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        close = df['Close']
        high = df['High']
        low = df['Low']
        
        bb_upper = bollinger_hband(close, window=self.bb_window, window_dev=self.bb_std).fillna(0).values
        bb_lower = bollinger_lband(close, window=self.bb_window, window_dev=self.bb_std).fillna(0).values
        
        kc_upper = keltner_channel_hband(high, low, close, window=self.kc_window, window_atr=self.kc_window, original_version=False).fillna(0).values
        kc_lower = keltner_channel_lband(high, low, close, window=self.kc_window, window_atr=self.kc_window, original_version=False).fillna(0).values
        
        # Squeeze On: Bollinger Bands inside Keltner Channels
        is_squeezed = (bb_upper < kc_upper) & (bb_lower > kc_lower)
        
        # Squeeze Fired: Prior bar squeezed, current bar expanding outside
        n = len(df)
        mask = np.zeros(n, dtype=bool)
        for i in range(1, n):
            if is_squeezed[i-1] and not is_squeezed[i]:
                mask[i] = True
                
        return BlockResult(self.name, self.category, self.tf, mask)
