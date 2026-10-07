"""
The yardstick: how big a move is, measured against the structure price is in (owner, 2026-10-06).

  "the pipe is about 25% im not talking about 1% lower lows. we already said moves are relative.
   even if the pipe is not perfectly horizontal because of a 1% decrease its noise compared to 25%."

The move running now is not always the right ruler. At 2024-08-02 price had dropped 12.2% from
the 07-29 peak, but it was dropping inside a ~25% pipe, and against 12% every step of that pipe
read as a trend and every 4% gap as two lines. The leg that ran INTO the latest peak or valley is
the structure's size - but only when it is read at that structure's own scale: at 7% the
53,486 -> 70,080 run is cut into wiggles and the leg into 07-29 reads 10.4%.

So the yardstick is the bigger of the move running now and the leg into the latest confirmed
peak or valley, re-read at the scale of the answer until it settles. "The scale" is a swing the
size of "the same move" (precedents.SIMILAR_LO) - no new number. At 2024-08-02:
12.2% -> 31.0% -> 25.7%, his "about 25%".
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from business_logic_services.precedents import SIMILAR_LO
from business_logic_services.swing_frame import turning_points_cached
from modules.shapes.swing_moves import leg_moves

MAX_STEPS = 8           # it settles in 1-3 steps on every date measured; this only stops a loop


def yardstick(df: pd.DataFrame, end: int, now_move: float, floor_size: float,
              cache: Optional[Dict] = None) -> float:
    """The size, in %, that "relative to the move" is measured against at `end`."""
    if now_move <= 0:
        return now_move
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    yard = now_move
    for _ in range(MAX_STEPS):
        size = round(max(SIMILAR_LO * yard / 100, floor_size), 3)
        tp = turning_points_cached(df, size, cache)
        known = np.flatnonzero((tp["conf"] <= end) & (tp["idx"] <= end))
        into = float(leg_moves(tp, high, low)[known[-1]]) if len(known) else 0.0
        new = max(now_move, into)
        if abs(new - yard) < 0.5:          # settled to within half a percent of the move
            return new
        yard = new
    return yard
