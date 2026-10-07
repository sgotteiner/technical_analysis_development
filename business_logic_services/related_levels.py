"""
Levels chosen BY THE RELATION, not decorated with one.

  "you try to predict the future based on the past so you have to find relations. not limit to
   less days." / "30 here 30 then." / "its not the time its the shape level and size."
                                                                       (owner, 2026-10-03 / 10-05)

The rule he has stated since the beginning: a level is worth looking at when the move that ran INTO
it is the size of the move running now. That is a relation between two moves, and it is what picks
the level. Everything else - how recent it is, how many dots it has, how long ago - is not the test.

  1. the move running now, and its size            the yardstick
  2. keep only the dots whose arriving leg RELATES to it (0.7x - 1.45x, "30 here 30 then")
  3. group those dots into levels, band taken from the move itself
  4. answer from where price is: the one it stands on, then the next ones up and down

What this replaces: clustering every dot in all of history by price, ranking by visits and
recency, and then writing a precedent sentence next to whatever came out. That produced a "current
support" built from two dots in 2021 and 2024 while the owner's support was the floor of the pipe
price is sitting in.
"""
from typing import Dict, List, Optional
import numpy as np
from business_logic_services.precedents import SIMILAR_HI, SIMILAR_LO, similar_move
from modules.shapes.price_zones import label_for, price_zones

PEAK = 1


def related_dots(moves: np.ndarray, now_move: float,
                 lo: float = SIMILAR_LO, hi: float = SIMILAR_HI) -> np.ndarray:
    """The dots whose arriving move is the same size as the one running now."""
    if now_move <= 0 or not len(moves):
        return np.zeros(len(moves), dtype=bool)
    return np.array([similar_move(float(m), now_move, lo, hi) for m in moves], dtype=bool)


def levels_by_relation(bars: np.ndarray, prices: np.ndarray, kinds: np.ndarray, moves: np.ndarray,
                       now_move: float, price_now: float, price_before: float, end: int,
                       band_pct: float, n_each: int = 3, min_dots: int = 1,
                       lo: float = SIMILAR_LO, hi: float = SIMILAR_HI) -> List[Dict]:
    """The ladder from where price is, built only from dots that relate to the move running now."""
    keep = related_dots(moves, now_move, lo, hi)
    if not keep.any():
        return []
    zones = price_zones(bars[keep], np.log(prices[keep]), kinds[keep], band_pct, price_now, end)
    zones = [z for z in zones if z["touches"] >= min_dots]
    if not zones:
        return []
    on = next((z for z in zones if z["at_price_now"]), None)
    above = sorted([z for z in zones if z is not on and z["price"] > price_now],
                   key=lambda z: z["price"])[:n_each]
    below = sorted([z for z in zones if z is not on and z["price"] < price_now],
                   key=lambda z: -z["price"])[:n_each]
    out = ([on] if on else []) + above + below
    for z in out:
        z["label"] = label_for(z["price"], price_now, price_before)
        z["from_relation"] = True
    return out


def roles_from(levels: List[Dict], price_now: float) -> List[Dict]:
    """Name each rung the way he names them, from where price is standing."""
    names_up = ["current resistance", "next resistance", "next next resistance", "further resistance"]
    names_down = ["current support", "next support", "next next support", "further support"]
    on = next((l for l in levels if l.get("at_price_now")), None)
    above = sorted([l for l in levels if l is not on and l["price"] > price_now], key=lambda l: l["price"])
    below = sorted([l for l in levels if l is not on and l["price"] < price_now], key=lambda l: -l["price"])
    out: List[Dict] = []
    if on is not None:
        out.append({**on, "role": on["label"]})          # came up to it = resistance, down = support
    for i, l in enumerate(above):
        out.append({**l, "role": names_up[min(i, len(names_up) - 1)]})
    for i, l in enumerate(below):
        out.append({**l, "role": names_down[min(i, len(names_down) - 1)]})
    return out
