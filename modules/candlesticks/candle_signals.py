"""
Candle patterns as masks, both directions - what an event can ask for as confirmation (owner,
2026-10-08: "what about candle patterns"). Nison's patterns, with the definitions the existing
blocks already use (hammer.py, engulfing.py, piercing.py), mirrored for the bearish side.

Research is not kind to them alone (Marshall, Young & Rose 2006: no profit on US stocks), so here
they only CONFIRM an event at a line - "a hammer at support" - never fire on their own.

  pin       hammer (bull): lower wick >= 2 bodies, upper wick <= half a body; shooting star (bear)
  engulfing the body swallows the previous opposite body
  piercing  opens under the previous low and closes past the middle of its body (bull); dark cloud
            cover (bear). Crypto trades around the clock, so the gap it needs is rare on BTC.
"""
from typing import Dict
import numpy as np
import pandas as pd

PATTERNS = ("pin", "engulfing", "piercing")


def candle_masks(df: pd.DataFrame) -> Dict[str, Dict[str, np.ndarray]]:
    """{pattern: {"up": mask, "down": mask}} over every bar; bar i uses bars i-1 and i only."""
    o, h, l, c = (df[k].to_numpy() for k in ("Open", "High", "Low", "Close"))
    po, ph, pl, pc = (np.concatenate([[np.nan], x[:-1]]) for x in (o, h, l, c))
    body = abs(c - o)
    top, bottom = np.maximum(o, c), np.minimum(o, c)
    up_wick, down_wick = h - top, bottom - l
    ok = (body > 0) & (h > l)
    pin_up = ok & (down_wick >= 2 * body) & (up_wick <= 0.5 * body)
    pin_down = ok & (up_wick >= 2 * body) & (down_wick <= 0.5 * body)
    bear_prev, bull_prev = pc < po, pc > po
    engulf_up = bear_prev & (c > o) & (c >= po) & (o <= pc)
    engulf_down = bull_prev & (c < o) & (c <= po) & (o >= pc)
    pbody = abs(pc - po)
    pierce_up = bear_prev & (c > o) & (o < pl) & (c > po - pbody / 2)
    pierce_down = bull_prev & (c < o) & (o > ph) & (c < po + pbody / 2)
    clean = lambda m: np.nan_to_num(m, nan=False).astype(bool)
    return {"pin": {"up": clean(pin_up), "down": clean(pin_down)},
            "engulfing": {"up": clean(engulf_up), "down": clean(engulf_down)},
            "piercing": {"up": clean(pierce_up), "down": clean(pierce_down)}}
