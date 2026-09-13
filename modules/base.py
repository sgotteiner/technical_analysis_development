from abc import ABC, abstractmethod
import pandas as pd
import numpy as np

class BlockResult:
    """
    Standardized Result output by any Block in any Category.
    Includes visual_data for rendering Candlestick boxes & Shape trendlines on TradingView charts.
    """
    def __init__(self, block_name, category, tf, mask, metadata=None, visual_data=None):
        self.block_name = block_name
        self.category = category
        self.tf = tf
        self.mask = mask  # numpy boolean array (True if signal fired)
        self.metadata = metadata or {}  # dict of additional details per bar
        self.visual_data = visual_data or {}  # dict mapping bar idx -> candle/shape bounds

class BaseBlock(ABC):
    """
    Abstract Base Class for all strategy blocks across Trend, Shape, Candlestick, and Indicator categories.
    """
    def __init__(self, name, category, tf):
        self.name = name
        self.category = category
        self.tf = tf
        
    @abstractmethod
    def evaluate(self, df_daily, df_1h) -> BlockResult:
        pass
