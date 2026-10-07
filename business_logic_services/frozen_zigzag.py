"""
The zigzag with its history frozen: every peak and valley is decided at the scale of the day it was
confirmed, and stays.

"i want the before 7d to be roughly like the date im looking" (owner, 2026-10-07). Read at today's
scale, the whole history was redrawn every day - the scale follows the move running now, which at
2024-03 flipped between a +77% rally (54% swings) and the dip inside it (7%), and a date shared a
median 71% of its zigzag with the date 7 days earlier. Every steady ruler measured instead either
fell to the 7% floor (every wiggle) or lost the dates he had approved. Freezing the past keeps
today's scale where it matched him and stops redrawing what already happened.
"""
from typing import Dict
import numpy as np
import pandas as pd
from business_logic_services.swing_frame import turning_points_cached
from modules.shapes.sr_turning_points import PEAK, turning_points
from modules.shapes.swing_moves import running_move

FIRST_DAY = 200          # before this there is too little history to read a move


def _scales(df: pd.DataFrame, end: int, floor_size: float, cache: Dict) -> Dict[int, float]:
    """The structure's scale on every day up to `end`, worked out once and kept."""
    from business_logic_services.trend_structure import read_structure   # it reads us back
    scales = cache.setdefault(("scales", floor_size), {})
    high, low, close = df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy()
    tp_floor = turning_points_cached(df, floor_size, cache)
    for day in range(FIRST_DAY, end + 1):
        if day in scales:
            continue
        move, _, _ = running_move(tp_floor, high, low, day, float(close[day]), close)
        trend = read_structure(df, day, move, floor_size, cache, frozen=False)[0] if move > 0 else None
        scales[day] = trend["size"] if trend else floor_size
    return scales


def frozen_points(df: pd.DataFrame, end: int, floor_size: float, cache: Dict) -> Dict[str, np.ndarray]:
    """Turning points as they were confirmed: (idx, kind, y, conf), like `turning_points` gives."""
    key = ("frozen", floor_size, end)
    if key in cache:
        return cache[key]
    scales = _scales(df, end, floor_size, cache)
    high, low = np.log(df["High"].to_numpy()), np.log(df["Low"].to_numpy())
    rows = []
    for size in set(scales.values()):
        tp = turning_points_cached(df, size, cache)
        for i, k, c in zip(tp["idx"], tp["kind"], tp["conf"]):
            if c <= end and scales.get(int(c)) == size:
                rows.append((int(i), int(k), int(c)))
    rows.sort()
    kept = []
    for i, k, c in rows:                  # one point per bar, peaks and valleys alternating
        if kept and kept[-1][0] == i:
            continue
        if kept and kept[-1][1] == k:     # two of a kind in a row: the more extreme one stands
            prev = kept[-1][0]
            if (high[i] > high[prev]) if k == PEAK else (low[i] < low[prev]):
                kept[-1] = (i, k, c)
            continue
        kept.append((i, k, c))
    idx = np.array([r[0] for r in kept], dtype=int)
    kind = np.array([r[1] for r in kept], dtype=int)
    y = np.where(kind == PEAK, high[idx], low[idx]) if len(idx) else np.array([])
    out = {"idx": idx, "kind": kind, "y": np.asarray(y, dtype=float),
           "conf": np.array([r[2] for r in kept], dtype=int)}
    cache[key] = out
    return out


def frozen_swing_points(df: pd.DataFrame, end: int, floor_size: float, cache: Dict) -> list:
    """The frozen points in the shape the level finder takes (as `swing_view.swing_points` gives)."""
    from modules.shapes.swing_moves import leg_moves
    tp = frozen_points(df, end, floor_size, cache)
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    moves = leg_moves(tp, high, low) if len(tp["idx"]) else np.array([])
    t = df.index
    return [{"bar": int(i), "time": int(t[int(i)].timestamp()),
             "price": float(high[i] if k == PEAK else low[i]),
             "kind": "peak" if k == PEAK else "valley", "move": float(m)}
            for i, k, m in zip(tp["idx"], tp["kind"], moves)]
