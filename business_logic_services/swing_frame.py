"""
The swing frame at one "now": the peaks and valleys the owner would be looking at on that day,
and what each one is worth.

Everything the setup layer needs is derived from the same five arrays, so they are built once and
passed around together instead of each function re-deriving them from the turning points (which is
how three functions here ended up with the same six-line preamble). Only points CONFIRMED by `end`
are ever in the frame, so nothing downstream can see the future.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np
import pandas as pd
from modules.shapes.sr_turning_points import turning_points, PEAK
from modules.shapes.swing_moves import leg_moves, running_move


def turning_points_cached(df: pd.DataFrame, size: float, cache: Optional[Dict] = None) -> Dict:
    """Turning points of the WHOLE df at `size`, shared between calls with different `end`:
    masking by `conf <= end` is what keeps that safe."""
    if cache is None:
        return turning_points(df, size)
    return cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))


@dataclass
class SwingFrame:
    """One day's view of the structure. `bars`, `prices` and `moves` line up index for index."""
    end: int
    size: float
    bars: np.ndarray            # the bar each confirmed point sits on
    prices: np.ndarray          # its high if a peak, its low if a valley
    kinds: np.ndarray           # +1 peak, -1 valley
    now_move: float             # the leg running now, in %, the yardstick everything is read against
    now_from_bar: float         # where that leg started
    now_direction: int          # +1 the leg is rising (price came UP to where it is), -1 falling
    price_now: float
    price_before: float         # ten days back, which is what names a level support or resistance
    moves: np.ndarray           # the leg that ran INTO each point - what a touch is worth
    index: pd.DatetimeIndex = field(repr=False)
    tp: Dict = field(repr=False)
    high: np.ndarray = field(repr=False)
    low: np.ndarray = field(repr=False)
    known: np.ndarray = field(repr=False)

    def __len__(self) -> int:
        return len(self.bars)

    def turned_at(self) -> float:
        """Where the move running now has got to: its high if rising, its low if falling - the
        level it ran INTO, which is what "came up to it" means."""
        seg = slice(int(self.now_from_bar), self.end + 1)
        return float(self.high[seg].max() if self.now_direction > 0 else self.low[seg].min())

    def day(self, bar: float) -> str:
        return self.index[int(bar)].strftime("%Y-%m-%d")

    def time(self, bar: float) -> int:
        return int(self.index[int(bar)].timestamp())


def swing_frame(df: pd.DataFrame, end: int, size: float, cache: Optional[Dict] = None) -> SwingFrame:
    tp = turning_points_cached(df, size, cache)
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    close = df["Close"].to_numpy()
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx = tp["idx"][known]
    now_move, now_from, now_dir = running_move(tp, high, low, end, float(close[end]), close)
    return SwingFrame(
        end=int(end), size=float(size),
        bars=idx.astype(float),
        prices=np.where(tp["kind"][known] == PEAK, high[idx], low[idx]).astype(float),
        kinds=tp["kind"][known],
        moves=leg_moves(tp, high, low)[known],
        now_move=float(now_move), now_from_bar=float(now_from), now_direction=int(now_dir),
        price_now=float(close[end]), price_before=float(close[max(0, end - 10)]),
        index=df.index, tp=tp, high=high, low=low, known=known)
