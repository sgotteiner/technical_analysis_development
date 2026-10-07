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


SMALL_BOUNCE = 0.5      # a leg this much smaller than the one before it has not started a new move
WICK = 0.5              # an extreme this far from its own close, as a share of the leg, is a spike


def _is_wick(bar: int, extreme: float, close: np.ndarray, leg: float) -> bool:
    """A turning point whose extreme the candle did not hold: price poked there and closed far
    away. "there was a candle who broke the support in a tail but got back and i ignored this
    spike" (owner, 2026-10-05). His case at 2026-02-13: low 60,000, close 70,580 - the close is
    17.6% off its own low while the leg into it was 18%, so the spike IS the leg. A real valley two
    days earlier closed 0.9% from its low.
    """
    if leg <= 0:
        return False
    return abs(float(close[bar]) / extreme - 1) >= leg * WICK


def running_move(tp: Dict[str, np.ndarray], high: np.ndarray, low: np.ndarray, end: int,
                 price_now: float = 0.0, close: np.ndarray = None) -> Tuple[float, int, int]:
    """The move price is in right now: from the turning point that STARTED it to where price is.
    Returns (percent, from_bar, direction), direction +1 for a rally.

    Not the last completed leg - the open part is the part that matters ("the trade IS the
    unfinished part") - and not necessarily the last turning point either. A small bounce does not
    start a new move: at 2026-02-13 price fell 97,924 -> 62,345 (-36%) and came back to 68,854
    (+10%), and he reads the move running now as the DESCENT, -29% from the peak, with the bounce
    inside it - his arrow is drawn 94,935 -> 67,071. So the walk goes back past any leg smaller
    than `SMALL_BOUNCE` of the one before it.

    Measured to PRICE NOW, not to the extreme reached: his arrow ends at today's price.
    """
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    idx, kind = tp["idx"][known], tp["kind"][known]
    if not len(idx):
        return 0.0, end, 0
    extreme = np.where(kind == PEAK, high[idx], low[idx]).astype(float)
    here = float(price_now) if price_now else float(high[end] if kind[-1] != PEAK else low[end])

    i = len(idx) - 1
    while i > 0:
        leg_now = abs(here / extreme[i] - 1)            # what has run since that point
        leg_before = abs(extreme[i] / extreme[i - 1] - 1)
        spike = close is not None and _is_wick(int(idx[i]), float(extreme[i]), close, leg_before)
        if not spike and (leg_before <= 0 or leg_now >= leg_before * SMALL_BOUNCE):
            break                                       # big enough to be a move of its own
        i -= 1                                          # a bounce, or a spike that came straight back
    start = int(idx[i])
    rising = here >= extreme[i]
    return abs(here / extreme[i] - 1) * 100, start, (1 if rising else -1)

