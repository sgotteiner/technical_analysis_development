"""
Composable, block-based strategy orchestrator.

A strategy is declared as a set of blocks + a combine rule. The orchestrator:
  1. evaluates each block on its NATIVE timeframe,
  2. connects every block onto the 1H trading timeframe via the no-lookahead
     aligner (BaseStrategy.align),
  3. combines them into (signals, macro_bull_mask, audit) for the backtest engine.

This is the ONLY sanctioned bridge from blocks -> backtestable signals, so the
alignment (no-lookahead) rule lives in exactly one place and can't be missed.
"""
import numpy as np
from strategies.base_strategy import BaseStrategy

TRADING_TF = "1H"


class ComposableStrategy(BaseStrategy):
    """
    trend_blocks : regime filters, AND'd together -> macro_bull_mask (the gate).
    entry_blocks : entry triggers, combined via `combine`.
    combine      : "ALL" (AND) | "ANY" (OR) | int N (N-of-M confluence).
    """
    def __init__(self, name, trend_blocks=None, entry_blocks=None, combine="ALL", params=None):
        super().__init__(name)
        self.trend_blocks = trend_blocks or []
        self.entry_blocks = entry_blocks or []
        self.combine = combine
        self.params = params or {}   # trade-management knobs (e.g. stop_loss_pct)

    def _mask_on_1h(self, block, df_daily, df_1h) -> np.ndarray:
        """Evaluate a block and connect its native-tf mask onto the 1H timeline."""
        res = block.evaluate(df_daily, df_1h)
        mask = np.asarray(res.mask)
        if block.tf == TRADING_TF:
            # Already on the trading timeframe; its value is known at that bar's close.
            return mask.astype(bool)
        src = df_daily if block.tf == "1D" else df_1h
        return self.align(src, df_1h, mask, fill_value=False)

    @staticmethod
    def _at_least(masks, n) -> np.ndarray:
        """True where at least `n` of the stacked masks are True."""
        return np.vstack(masks).sum(axis=0) >= n

    def _need(self, num_blocks: int) -> int:
        if self.combine == "ALL":
            return num_blocks
        if self.combine == "ANY":
            return 1
        return int(self.combine)  # N-of-M confluence

    def generate_signals(self, df_daily, df_1h):
        n_bars = len(df_1h)

        # 1) Regime gate: ALL trend blocks must agree.
        if self.trend_blocks:
            trend_masks = [self._mask_on_1h(b, df_daily, df_1h) for b in self.trend_blocks]
            macro_bull_mask = self._at_least(trend_masks, len(trend_masks))
        else:
            macro_bull_mask = np.ones(n_bars, dtype=bool)

        # 2) Entry trigger: combine entry blocks per rule (default: follow the regime).
        if self.entry_blocks:
            entry_masks = [self._mask_on_1h(b, df_daily, df_1h) for b in self.entry_blocks]
            entry_trigger = self._at_least(entry_masks, self._need(len(entry_masks)))
        else:
            entry_trigger = macro_bull_mask

        signals = (macro_bull_mask & entry_trigger).astype(int)
        audit = {
            "trend_blocks": [b.name for b in self.trend_blocks],
            "entry_blocks": [b.name for b in self.entry_blocks],
            "combine": self.combine,
        }
        return signals, macro_bull_mask, audit


class ComposedSupertrendStrategy(ComposableStrategy):
    """
    Example composed strategy: daily SuperTrend regime + 1H RSI ceiling filter.
    Proves the block -> aligner -> combine -> engine path end-to-end.
    """
    def __init__(self, params=None):
        from modules.trends.supertrend import SuperTrendBlock
        from modules.indicators.rsi_filter import RsiFilterBlock
        super().__init__(
            name="Composed SuperTrend + RSI",
            trend_blocks=[SuperTrendBlock(tf="1D", period=10, multiplier=3.0)],
            entry_blocks=[RsiFilterBlock(tf="1H", period=14, max_rsi=72)],
            combine="ALL",
        )
