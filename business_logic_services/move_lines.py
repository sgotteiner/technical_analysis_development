"""
Lines ranked by the move that ran into them (the owner's rule, 2026-10-03).

A cluster of touches is still a cluster of touches (modules/shapes/price_zones.py). What changes is
what a touch is WORTH and which touches belong to the line at all:

  worth    the leg that arrived at it, not its own wiggle - "the move this line resisted was about
           10%" for the 67 line, against ~28% for the line price is working now
  belongs  "the earlier it is the bigger the move it has to relate to": a touch whose move is too
           small for its age is not part of this line, which is what stops a line being drawn from
           2021 - "i woudnt draw it from that long before"
  matters  "its the same move and same resistance" - a line is relevant now when the moves it
           turned back are the size of the move running now

So the answer is not a flat list of prices: each line comes back with its move, how that compares
with the move running now, and the span its surviving touches actually cover.
"""
from typing import Dict, List, Optional
import numpy as np
from modules.shapes.price_zones import label_for, price_zones
from modules.shapes.swing_moves import required_move


def _term(ratio: float) -> str:
    """How a line stands against the move running now, in his words."""
    if ratio >= 0.75:
        return "this move"          # the 80k line: same move, same resistance
    return "short term" if ratio >= 0.35 else "far smaller"


def lines_by_move(x: np.ndarray, y: np.ndarray, kinds: np.ndarray, moves: np.ndarray,
                  band_pct: float, price_now: float, price_before: float, end: float,
                  current_move: float, age_scale: float = 365.0, min_touches: int = 2,
                  top: int = 0) -> List[Dict]:
    """`moves[i]` is the leg that ran into the point at `x[i]`. Returns the lines, strongest match
    to the move running now first."""
    if not len(x) or current_move <= 0:
        return []
    move_of = {float(b): float(m) for b, m in zip(x, moves)}
    out: List[Dict] = []
    for z in price_zones(x, y, kinds, band_pct, price_now, end):
        bars = [float(b) for b in z["points"]]
        ages = np.array([end - b for b in bars], dtype=float)
        mv = np.array([move_of.get(b, 0.0) for b in bars])
        keeps = mv >= required_move(ages, current_move, age_scale)
        if int(keeps.sum()) < min_touches:
            continue                      # nothing left that is big enough for how old it is
        kept_bars = [b for b, k in zip(bars, keeps) if k]
        kept_moves = mv[keeps]
        median_move = float(np.median(kept_moves))
        ratio = median_move / current_move
        out.append({
            "price": z["price"], "y": z["y"], "low": z["low"], "high": z["high"],
            "move": median_move, "biggest_move": float(kept_moves.max()),
            "vs_now": ratio, "term": _term(ratio),
            "touches": len(kept_bars), "dropped": int((~keeps).sum()),
            "first": min(kept_bars), "last": max(kept_bars), "points": kept_bars,
            "at_price_now": z["at_price_now"],
            "label": label_for(z["price"], price_now, price_before),
            "visits": z["visits"],
        })
    # The picture is the LADDER from where price is - "what is my support, my resistance, whats the
    # next ones" - so the rungs are chosen by distance from price, not by a global ranking. Ranking
    # by move-match alone put 2019 levels at $6,927 on the chart, which is not a trader's answer.
    # Within a rung, the move tells him whether it is this move's line or a smaller one's.
    out.sort(key=lambda l: (not l["at_price_now"], abs(np.log(l["price"] / price_now))))
    # one spacing pass, as the levels rule has: never two lines closer than the band
    gap = np.log(1 + band_pct / 100)
    kept: List[Dict] = []
    for l in out:
        if not any(abs(np.log(l["price"] / k["price"])) < gap for k in kept):
            kept.append(l)
    return kept[:top] if top else kept


def ladder_by_move(lines: List[Dict], price_now: float, n_each: int = 3) -> Dict:
    """The trade the lines describe, read from where price is: the line it stands on, the rungs
    above in order (targets) and the first below (the stop - "the previous support obviously")."""
    on = next((l for l in lines if l["at_price_now"]), None)
    rest = [l for l in lines if l is not on]
    above = sorted([l for l in rest if l["price"] > price_now], key=lambda l: l["price"])
    below = sorted([l for l in rest if l["price"] < price_now], key=lambda l: -l["price"])
    entry = on["price"] if on else (below[0]["price"] if below else None)
    stop = (below[0] if on else (below[1] if len(below) > 1 else None))
    risk = None if (entry is None or stop is None) else (entry - stop["price"]) / entry * 100
    targets = []
    for t in above[:n_each]:
        targets.append({"price": t["price"], "move": t["move"], "vs_now": t["vs_now"],
                        "reward_pct": None if entry is None else (t["price"] / entry - 1) * 100,
                        "r": None if not risk else (t["price"] / entry - 1) * 100 / risk})
    return {"price_now": price_now, "on": on, "entry": entry,
            "stop": None if stop is None else stop["price"], "risk_pct": risk,
            "targets": targets, "below": [l["price"] for l in below[:n_each]]}
