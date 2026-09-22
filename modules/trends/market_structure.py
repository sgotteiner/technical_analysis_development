import numpy as np
from modules.base import BaseBlock, BlockResult

BULL, SIDEWAYS, BEAR = 1, 0, -1


class MarketStructureBlock(BaseBlock):
    """
    Category 1: Trend Classifier (Market Structure regime: bull / bear / sideways)

    Swing High (SH) / Swing Low (SL) = the extreme of `pivot_span` bars on each side.
    A swing is only CONFIRMED once those `pivot_span` bars after it have closed, and
    is used from that bar on — never earlier (no lookahead).

    Regime per bar, from the latest two confirmed SH and SL (Break of Structure first):
    - BULL:     close breaks above the last SH, else Higher High + Higher Low
    - BEAR:     close breaks below the last SL, else Lower High + Lower Low
    - SIDEWAYS: mixed structure, or fewer than two confirmed SH/SL yet

    mask = (state == BULL). metadata["state"] holds the 3-state regime (+1 / 0 / -1).
    """
    def __init__(self, tf='1D', pivot_span=5):
        super().__init__(name=f"Market Structure ({tf} HH/HL & BOS)", category="Trend", tf=tf)
        self.pivot_span = pivot_span

    def find_pivots(self, high, low):
        """Return (swing_highs, swing_lows) as lists of (pivot_idx, price, confirmed_idx)."""
        n, w = len(high), self.pivot_span
        sh, sl = [], []
        for i in range(w, n - w):
            left, right = slice(i - w, i), slice(i + 1, i + w + 1)
            if high[i] >= high[left].max() and high[i] >= high[right].max():
                sh.append((i, high[i], i + w))
            if low[i] <= low[left].min() and low[i] <= low[right].min():
                sl.append((i, low[i], i + w))
        return sh, sl

    @staticmethod
    def classify(close, sh_prev, sh_last, sl_prev, sl_last):
        """Regime from the last two confirmed swing highs/lows and the current close."""
        if close > sh_last:
            return BULL
        if close < sl_last:
            return BEAR
        if sh_last > sh_prev and sl_last > sl_prev:
            return BULL
        if sh_last < sh_prev and sl_last < sl_prev:
            return BEAR
        return SIDEWAYS

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        df = df_daily if self.tf == '1D' else df_1h
        high, low, close = df['High'].values, df['Low'].values, df['Close'].values
        n = len(df)
        sh, sl = self.find_pivots(high, low)

        state = np.full(n, SIDEWAYS, dtype=int)
        ready = np.zeros(n, dtype=bool)
        h_seen, l_seen = [], []   # prices of swings confirmed so far
        hi = li = 0
        for i in range(n):
            # Admit swings whose confirmation bar has closed (confirmed_idx <= i).
            while hi < len(sh) and sh[hi][2] <= i:
                h_seen.append(sh[hi][1]); hi += 1
            while li < len(sl) and sl[li][2] <= i:
                l_seen.append(sl[li][1]); li += 1
            if len(h_seen) >= 2 and len(l_seen) >= 2:
                ready[i] = True
                state[i] = self.classify(close[i], h_seen[-2], h_seen[-1], l_seen[-2], l_seen[-1])

        # Native-timeframe mask; alignment is owned by the strategy orchestrator.
        return BlockResult(self.name, self.category, self.tf, state == BULL,
                           metadata={"state": state, "ready": ready})
