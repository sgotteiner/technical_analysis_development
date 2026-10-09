"""
What a level's strength is made of - each part a concept that can be switched on or off, and each
shown on its own so the card can say what made a line (owner, 2026-10-08: "i wanna know what made
the algorithm draw each line. which peaks and valleys it used, scores, whatever").

  pivots   how many peaks and valleys it was grouped from          x20  (S/R Channels)
  bars     bars of the last LOOKBACK whose high or low touched it  x1   (S/R Channels)
  sweeps   bars whose wick went through it and closed back         x20  (LuxAlgo, SMC - his tail)
  round    on a whole 10,000 (at today's prices)                   +20  (Osler)
  measured our measured chance of a turn (level_strength), in %    x1

The weights are the S/R Channels script's units (20 a pivot, 1 a bar) carried to the others. They
are NOT measured: the backtest is what will weigh them.
"""
from typing import Dict, Iterable
import numpy as np
from modules.shapes.sr_channels import LOOKBACK, PER_PIVOT, bars_inside

PARTS = ("pivots", "bars", "sweeps", "round", "measured")
WEIGHT = {"pivots": PER_PIVOT, "bars": 1, "sweeps": PER_PIVOT, "round": PER_PIVOT, "measured": 1}
ROUND_TOUCH_PCT = 1.4        # the page's touch zone


def _sweeps(lo: float, hi: float, high, low, close, end: int) -> int:
    """Bars up to `end` that poked through the level and closed back on the side they came from."""
    h, l, c = high[:end + 1], low[:end + 1], close[:end + 1]
    under = (l < lo) & (c >= lo) & (h >= lo)          # swept below, closed back on or above it
    over = (h > hi) & (c <= hi) & (l <= hi)           # swept above, closed back on or below it
    return int((under | over).sum())


def _round(price: float) -> int:
    unit = 10 ** np.floor(np.log10(price))
    return int(abs(price - round(price / unit) * unit) / price * 100 <= ROUND_TOUCH_PCT)


def level_parts(c: Dict, high, low, close, end: int, on: Iterable[str],
                measured: float = 0.0) -> Dict:
    """The parts that are switched on, their raw counts, and the score they add up to."""
    on = set(on)
    recent = slice(max(0, end - LOOKBACK), end + 1)
    raw = {"pivots": len({b for b, _ in c["members"]}),
           "bars": bars_inside(c, high[recent], low[recent]),
           "sweeps": _sweeps(c["lo"], c["hi"], high, low, close, end),
           "round": _round((c["lo"] + c["hi"]) / 2),
           "measured": round(measured * 100)}
    parts = {k: raw[k] for k in PARTS if k in on}
    return {"parts": parts, "score": int(sum(WEIGHT[k] * v for k, v in parts.items()))}


def parts_text(parts: Dict) -> str:
    """'3 pivots x20 + 21 bars + 1 sweep x20' - the score in words."""
    names = {"pivots": "pivots", "bars": "bars touching", "sweeps": "wick sweeps",
             "round": "round number", "measured": "measured %"}
    return " + ".join(f"{v} {names[k]}" + (f" x{WEIGHT[k]}" if WEIGHT[k] != 1 else "")
                      for k, v in parts.items()) or "no strength parts on"
