"""
Abstract Base Class for all trading strategies.

Provides the one sanctioned, no-lookahead way to connect a higher-timeframe
signal onto the trading timeframe (`align`). Every multi-timeframe strategy must
route cross-timeframe mapping through it, so lookahead can never be reintroduced.
"""
from abc import ABC, abstractmethod
from typing import Any
import numpy as np
import pandas as pd
from helpers.timestamp_helpers import align_timeframe_signal


class BaseStrategy(ABC):
    def __init__(self, name: str):
        self.name = name

    def align(
        self,
        htf_df: pd.DataFrame,
        ltf_df: pd.DataFrame,
        htf_signal: Any,
        fill_value: Any = False,
    ) -> np.ndarray:
        """
        Connect a higher-timeframe (HTF) signal onto the lower-timeframe (LTF)
        bars you trade on, with NO lookahead. Each LTF bar sees only the most
        recent HTF bar that has already CLOSED. Use this for EVERY cross-
        timeframe mapping.
        """
        return align_timeframe_signal(htf_df, ltf_df, htf_signal, fill_value=fill_value)

    @abstractmethod
    def generate_signals(self, df_daily, df_1h):
        """
        Compute each timeframe's signal independently, connect them via `align`,
        and return (signals, macro_bull_mask, audit_log) aligned to df_1h.
        """
        raise NotImplementedError
