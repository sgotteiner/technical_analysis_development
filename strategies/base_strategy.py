from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    """
    Abstract Base Class for all Strategy Orchestrators in strategies/
    """
    def __init__(self, name):
        self.name = name
        self.trend_blocks = []
        self.shape_blocks = []
        self.candlestick_blocks = []
        self.indicator_blocks = []
        
    @abstractmethod
    def generate_signals(self, df_daily, df_1h):
        """
        Orchestrates block evaluations and returns (signals, macro_bull_mask, audit_log)
        """
        pass
