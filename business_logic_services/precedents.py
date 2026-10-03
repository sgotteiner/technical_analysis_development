"""
Finding the precedent — the owner's search, in his words (2026-10-03):

  "you trade the current state right? so you look for things related to current state. you have a
   peak at a certain level and size you look it in the past. thats it ... 30 here 30 then. or
   whatever you can find in that level. you found something similar like i did and described you
   stop. you dont check the entire history."

So this is a BACKWARD SEARCH WITH AN EARLY EXIT, not a filter over all of history:

  take the current state   price is at a level, after a move of some size
  walk back                through the times price was at that same level
  stop at the match        the first one whose move is a similar size - that is the precedent
  nothing similar          take what is there anyway ("or whatever you can find in that level")

Two things it is NOT, both corrected by him: it is not a limit in days ("i didnt mention age"), and
it is not judged against the era it happened in ("nothing for then. you dont compare with previous
era. 30 here 30 then").
"""
from typing import Dict, List, Optional
import numpy as np

SIMILAR_LO, SIMILAR_HI = 0.7, 1.45      # "30 here 30 then" - how close counts as the same move


def similar_move(move: float, current_move: float,
                 lo: float = SIMILAR_LO, hi: float = SIMILAR_HI) -> bool:
    if current_move <= 0:
        return False
    return lo <= move / current_move <= hi


def precedent_at(level_price: float, current_move: float, bars: np.ndarray, prices: np.ndarray,
                 moves: np.ndarray, band_pct: float, before_bar: float,
                 lo: float = SIMILAR_LO, hi: float = SIMILAR_HI) -> Optional[Dict]:
    """The previous time price was at this level, walking back from `before_bar` and STOPPING at
    the first whose move is the same size. Returns that one, or the most recent one at the level
    when none of them matches, or None when price has never been here before.

    `checked` says how many it had to look at - the point of stopping is that this stays small.
    """
    band = np.log(1 + band_pct / 100)
    at_level = np.flatnonzero((np.abs(np.log(prices / level_price)) <= band) & (bars < before_bar))
    if not len(at_level):
        return None
    fallback, checked = None, 0
    for j in at_level[::-1]:                      # backwards from the most recent
        checked += 1
        hit = {"bar": float(bars[j]), "price": float(prices[j]), "move": float(moves[j]),
               "vs_now": float(moves[j] / current_move) if current_move > 0 else 0.0,
               "checked": checked, "matched": True}
        if similar_move(moves[j], current_move, lo, hi):
            return hit                            # found something similar -> stop
        if fallback is None:
            fallback = {**hit, "matched": False}
    return {**fallback, "checked": checked}       # nothing similar: whatever is at that level


def picture_starts_at(level_price: float, current_move: float, bars: np.ndarray,
                      prices: np.ndarray, moves: np.ndarray, band_pct: float,
                      before_bar: float) -> float:
    """How far back the picture reaches: to the precedent of the level price is working now, and
    no further. That is where he stopped looking, so it is where the chart's story begins."""
    p = precedent_at(level_price, current_move, bars, prices, moves, band_pct, before_bar)
    return before_bar if p is None else p["bar"]


def targets_above(bars: np.ndarray, prices: np.ndarray, price_now: float, band_pct: float,
                  n: int = 2) -> List[Dict]:
    """Where a breakout goes: "the next breakout is the previous peak above that point which was
    96 or 108" (owner). Walking back from now, the previous peaks above price, nearest first - and
    it stops once it has `n` of them, like the rest of the search."""
    band = np.log(1 + band_pct / 100)
    out: List[Dict] = []
    above = float(np.log(price_now)) + band            # past the shelf price is on already
    for j in np.argsort(bars)[::-1]:                   # walking BACK in time, as he does
        if np.log(prices[j]) <= above:
            continue
        out.append({"price": float(prices[j]), "bar": float(bars[j]),
                    "reward_pct": (prices[j] / price_now - 1) * 100})
        if len(out) >= n:
            break
        above = float(np.log(prices[j])) + band        # then the previous peak above THAT one
    return out


def levels_with_precedents(bars: np.ndarray, prices: np.ndarray, moves: np.ndarray,
                           candidates: List[float], current_move: float, band_pct: float,
                           now_bar: float, price_now: float) -> List[Dict]:
    """For each level in play now, the one precedent behind it. Ranked from where price is."""
    out: List[Dict] = []
    for level in candidates:
        if any(abs(np.log(level / k["price"])) < np.log(1 + band_pct / 100) for k in out):
            continue                              # one line per level
        p = precedent_at(level, current_move, bars, prices, moves, band_pct, now_bar)
        out.append({
            "price": float(level),
            "precedent": p,
            "matched": bool(p and p["matched"]),
            "checked": 0 if p is None else p["checked"],
            "label": "resistance" if level > price_now else "support",
            "distance_pct": (level / price_now - 1) * 100,
        })
    out.sort(key=lambda l: abs(l["distance_pct"]))
    return out
