"""
The move that ran into a point — the owner's measure of what a touch is worth (2026-10-03).

  "previous 80k resistance after about 25% move like the current move that is now on this
   resistance. important line because its the same move and same resistance."

A touch is not worth its own little wiggle; it is worth the leg that arrived at it. Measured on his
own example, both legs come out the same: the May 2026 peak ran 65,000 -> 82,850 (+27.5%) and the
leg running now ran 64,166 -> 82,300 (+28.3%), off two valleys 1.3% apart. Same move, same
resistance - which is why he calls that line the important one.

The leg still in progress counts, including the part that has not finished: the trade IS the
unfinished part (owner, 2026-10-03, answering which of the two readings was meant).
"""
from typing import Dict, Tuple
import numpy as np

PEAK = 1


def leg_moves(tp: Dict[str, np.ndarray], high: np.ndarray, low: np.ndarray) -> np.ndarray:
    """For every turning point, how far price ran to arrive at it, in percent.

    The leg is from the previous turning point (the opposite kind) to this one, measured extreme
    to extreme. The first point has no leg before it and gets 0.
    """
    idx, kind = tp["idx"], tp["kind"]
    if not len(idx):
        return np.array([])
    extreme = np.where(kind == PEAK, high[idx], low[idx])
    out = np.zeros(len(idx))
    out[1:] = np.abs(extreme[1:] / extreme[:-1] - 1) * 100
    return out


def running_move(tp: Dict[str, np.ndarray], high: np.ndarray, low: np.ndarray,
                 end: int) -> Tuple[float, int, int]:
    """The leg price is in right now: from the last confirmed turning point to the extreme reached
    since, including today. Returns (percent, from_bar, direction) with direction +1 for a rally.

    Not the last COMPLETED leg: he reads the picture as a move still deciding - "it could stay in
    the pipe or breakout" - so the open part of the leg is the part that matters.
    """
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx, kind = tp["idx"][known], tp["kind"][known]
    if not len(idx):
        return 0.0, end, 0
    start = int(idx[-1])
    rising = kind[-1] != PEAK                       # off a valley, price is going up
    if rising:
        base = float(low[start])
        reached = float(np.max(high[start:end + 1]))
    else:
        base = float(high[start])
        reached = float(np.min(low[start:end + 1]))
    return abs(reached / base - 1) * 100, start, (1 if rising else -1)


def required_move(age_days: np.ndarray, current_move: float, age_scale: float) -> np.ndarray:
    """How big a touch's move must be to still count, given how long ago it was.

    "the earlier it is the bigger the move it has to relate to" (owner). One knob: at `age_scale`
    days old a touch has to match the move running now; nearer touches need proportionally less,
    older ones proportionally more. The knob is meant to be SEARCHED against his verdicts, not
    chosen - which is why there is only one of it.
    """
    return current_move * np.asarray(age_days, dtype=float) / max(age_scale, 1e-9)
