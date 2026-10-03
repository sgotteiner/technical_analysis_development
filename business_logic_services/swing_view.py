"""
The structure, ready to draw: each peak and valley as a dot, and each one as the journey it is.

Shape only - no rule decides anything here. What a dot is WORTH (the leg that ran into it) comes
from the frame; which dots make a line is business_logic_services/line_rules.py.
"""
from typing import Dict, Optional
import pandas as pd
from business_logic_services.swing_frame import swing_frame, turning_points_cached
from modules.shapes.swing_boxes import swing_boxes
from modules.shapes.sr_turning_points import PEAK


def swing_points(df: pd.DataFrame, end: int, size: float, cache: Optional[Dict] = None,
                 lookback: Optional[int] = None) -> list:
    """The peaks and valleys of a `size` zigzag confirmed by `end`, each with the move that ran
    into it and the move running now (owner, 2026-10-03)."""
    f = swing_frame(df, end, size, cache)
    keep = range(len(f))
    if lookback:
        keep = [i for i in keep if f.bars[i] >= end - lookback + 1]
    return [{"bar": int(f.bars[i]), "time": f.time(f.bars[i]), "price": float(f.prices[i]),
             "kind": "peak" if f.kinds[i] == PEAK else "valley",
             "move": float(f.moves[i]), "running_move": f.now_move} for i in keep]


def swing_box_view(df: pd.DataFrame, end: int, size: float, cache=None,
                   from_bar: float = 0.0) -> list:
    """Each peak and valley as the journey it is - support to resistance to support, and the
    opposite for a valley (owner, 2026-10-03: "i need to see what you do")."""
    tp = turning_points_cached(df, size, cache)
    boxes = swing_boxes(tp, df["High"].to_numpy(), df["Low"].to_numpy(), end, from_bar)
    t = df.index
    return [{**b, "from_time": int(t[b["from_bar"]].timestamp()),
             "to_time": int(t[b["to_bar"]].timestamp())} for b in boxes]
