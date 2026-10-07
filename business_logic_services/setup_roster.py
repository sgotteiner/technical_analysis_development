"""
The setup he asks for, and nothing else (owner, 2026-10-05):

  "i want a last trend line which is the last line with at least 2 peaks and valleys at changing
   levels ... if we are not on a level i want the above and below sr lines and if we are i want
   that level too which based on the trend you classify it ... i dont want a million lines."

So the roster is at most four lines:

  the trend        its DIRECTION comes from the structure (trend_state.last_trend: two peaks and
                   two valleys that agree), and the LINE is the most recent trend line on that
                   side. Broken is allowed - breaking a trend does not end it until two new peaks
                   and valleys say otherwise.
  above / below    the nearest level over price and the nearest under it
  on               the level price is standing on, if it is on one, named by the trend:
                   in a down trend it is resistance, in an up trend support

Everything else the layer can find - more rungs, more diagonals - is not in the answer.
"""
from typing import Dict, List, Optional
import numpy as np
from business_logic_services.precedents import SIMILAR_HI
from business_logic_services.trend_state import DOWN, UP, at_bar, last_trend

ON_LEVEL_PCT = 1.5          # price is "on" a level when it is this close to it


def _nearest(levels: List[Dict], price: float, above: bool) -> Optional[Dict]:
    side = [l for l in levels if (l["price"] > price) == above
            and abs(l["price"] / price - 1) * 100 > ON_LEVEL_PCT]
    if not side:
        return None
    return min(side, key=lambda l: abs(np.log(l["price"] / price)))


def _trend_line(trend: Dict, candidates: List[Dict], end: int) -> Optional[Dict]:
    """The most recent trend line that runs the way the structure says."""
    want = "resistance" if trend["direction"] == DOWN else "support" if trend["direction"] == UP else None
    pool = [t for t in candidates if want is None or t["role"] == want]
    if not pool:
        return None
    return max(pool, key=lambda t: (t["touches"], t["first"]))


def _wall(bars: List[float], prices: List[float], name: str) -> Dict:
    """One wall of the range price is in, as a level made of the range's own peaks or valleys."""
    return {"price": float(np.exp(np.mean(np.log(prices)))), "points": list(bars),
            "point_prices": list(prices), "touches": len(bars), "visits": len(bars),
            "high": float(max(prices)), "low": float(min(prices)),
            "y": float(np.mean(np.log(prices))), "history": 0, "anchor": max(bars),
            "merged_from": len(bars), "from_history": False,
            "first": min(bars), "last": max(bars), "at_price_now": False, "wall": name}


def _range_walls(trend: Dict, price_now: float, levels: List[Dict]) -> List[Dict]:
    """Inside a range the lines are its walls: "just a sideways range ... as a trader i would
    assume it would just go to the resistance" (2026-10-06, at 2024-08-02, where three lines 4-5%
    apart inside a 25% pipe were drawn instead). Price is ON a wall only when it is at it, and then
    the next line beyond that wall is drawn too: "if the price itself is on an important level draw
    it as support or resistance like you do and draw another line which would be the next"."""
    ceiling = _wall(trend["peaks"], trend["peak_prices"], "ceiling")
    floor = _wall(trend["valleys"], trend["valley_prices"], "floor")
    out = []
    for w, beyond_above in ((ceiling, True), (floor, False)):
        if abs(w["price"] / price_now - 1) * 100 > ON_LEVEL_PCT:
            out.append(w)
            continue
        out.append({**w, "on": True})
        past = [l for l in levels
                if (l["low"] > w["high"] if beyond_above else l["high"] < w["low"])]
        nxt = _nearest(past, w["price"], beyond_above)
        if nxt is not None:
            out.append(nxt)
    return out


def _flat_top(levels: List[Dict], trend: Optional[Dict], price_now: float,
              flat_pct: float) -> List[Dict]:
    """In an up trend the resistance above is its LATEST PEAK - the high it has to break - whenever
    price is under it. "should have been at the peak of about 31400" (2023-04-21); his 2023-08-11
    flat top at ~31,450 and the 69,538 he liked at 2024-10-25 are that high too. A cluster already
    on it stays as it is; the levels between price and it go.

    Only the top of an UP trend: the mirror (a flat floor under a down trend) was measured and moved
    the supports he approved at 2025-04-25, 2026-05-15 and 2026-09-04."""
    if trend is None or trend.get("direction") != UP or not trend.get("peak_prices"):
        return levels
    top = _wall(trend["peaks"][-1:], trend["peak_prices"][-1:], "ceiling")
    if price_now >= top["price"]:
        return levels                                   # price is at or past it
    on_it = [l for l in levels if abs(l["price"] / top["price"] - 1) * 100 <= ON_LEVEL_PCT]
    rest = [l for l in levels if not price_now < l["price"] < top["high"] and l not in on_it]
    return rest + (on_it or [top])


def _reach(trend: Dict, price_now: float, end: int, move_pct: float) -> Dict:
    """Mark a trend line further from price than a move of the same size can carry as `far` - drawn,
    but marked, never hidden. Hiding it (2026-10-06, after "the trend is so far it is not related to
    the trade so either draw it better ... or dont draw it" at 2023-04-21) left two flat lines that
    read as a pipe with no trend, which his rule forbids: "if currently its a sideways range pipe
    and there is no up or down trend i want the previous trend" (2026-10-07, at 2023-03-24).
    "The same size" is the backward search's own window (precedents.SIMILAR_HI)."""
    away = abs(np.log(at_bar(trend, end) / price_now))
    far = move_pct > 0 and away > np.log(1 + SIMILAR_HI * move_pct / 100)
    return {**trend, "far": bool(far), "away_pct": float(abs(at_bar(trend, end) / price_now - 1) * 100)}


def keep_roster(levels: List[Dict], trends: List[Dict], bars: np.ndarray, prices: np.ndarray,
                kinds: np.ndarray, price_now: float, end: int, flat_pct: float = 2.0,
                trend: Optional[Dict] = None, turned_at: float = 0.0, band_pct: float = 0.0,
                move_pct: float = 0.0, move_from_bar: float = 0.0, min_visits: int = 2):
    """Cut the answer down to what he asks for: the level above, the level below, the one price is
    on, and ONE trend line - the one running the way the structure says.

    "i dont want no next and i want the last trend. should be 3 or 4 if price is on the level"
    (owner, 2026-10-05).

    `trend`: the trend read at the scale of the move (trend_structure.structural_trend). When it is
    given it IS the answer - no fitted line replaces it for sitting nearer price, which is how the
    2026-02-13 line came to run through price at 68,791 instead of over the lower peaks.
    """
    # the trend line is drawn only when there IS a trend: "its sideways. draw only whats there"
    # (2026-10-06) - a range is its walls, not a 1% "trend" along the ceiling
    if trend is not None and trend.get("inside"):
        # the range is the answer; the trend before it is drawn when it is a trend and in reach
        prev = trend.get("previous")
        # and on its own side - an up line under price, a down line over it: once price is past it
        # the range has replaced it ("up trends support (above the graph) or down trends below ...
        # seem to add noise", 2026-09-24). 2025-10-03 drew an up line at 142,764, 17% over price.
        keep_prev = prev is not None and (at_bar(prev, end) <= price_now) == (prev["direction"] == UP)
        return _range_walls(trend, price_now, levels), [_reach(prev, price_now, end, move_pct)] if keep_prev else []
    if move_from_bar > 0:
        # a level comes from a PREVIOUS support or resistance: the move running now is not its own
        # evidence. At 2022-07-22 the resistance above was 24,286 - a 2020 wiggle price ran straight
        # through, plus this move's own high two days earlier: "the current resistance is not from
        # a previous resistance at all. the point it touched wasnt a resistance" (2026-10-07). His
        # line is the ~29k flip, which was there as 28,827.
        levels = [l for l in levels if l.get("wall")
                  or sum(1 for b in l.get("points", []) if b < move_from_bar) >= min_visits]
    if turned_at > 0 and band_pct > 0:
        # a level price is merely passing through is not one it is ON: the level price is on is the
        # one the move running now ran into ("came up to it"). At 2024-10-25 the move turned at
        # 69,520 and price fell back through 66,867 - "i dont think its on a line i would remove it".
        levels = [l for l in levels if abs(l["price"] / price_now - 1) * 100 > ON_LEVEL_PCT
                  or abs(l["price"] / turned_at - 1) * 100 <= band_pct]
    levels = _flat_top(levels, trend, price_now, flat_pct)
    on = next((l for l in levels if abs(l["price"] / price_now - 1) * 100 <= ON_LEVEL_PCT), None)
    if on is not None:
        on = {**on, "on": True}      # the card reads this mark - one answer to "is price on it"
    keep = [l for l in (on, _nearest(levels, price_now, True), _nearest(levels, price_now, False))
            if l is not None]
    if trend is not None:
        return keep, [_reach(trend, price_now, end, move_pct)] if trend["direction"] in (UP, DOWN) else []
    structure = last_trend(bars, prices, kinds, flat_pct)
    if structure is None:
        return keep, []
    # the structure IS the line - the peaks in a down trend or a range, the valleys in an up one.
    # Picking a fitted line that merely agrees with the direction put a rising "support" at 99,513
    # on a chart whose structure was horizontal at 72,310 (2026-04-10): the card then argued with
    # itself. A fitted line is only used when it runs on the same side AND stays nearer price.
    if structure["direction"] not in (UP, DOWN):
        return keep, []                     # sideways: "draw only whats there"
    line = {**structure, "touches": structure["touches"]}
    fitted = _trend_line(structure, trends, end)
    if fitted is not None:
        near = lambda t: abs(np.log(at_bar(t, end) / price_now))
        if near(fitted) < near(line):
            line = {**fitted, "direction": structure["direction"], "structure": structure}
    return keep, [line]


def roster(levels: List[Dict], trend_candidates: List[Dict], bars: np.ndarray, prices: np.ndarray,
           kinds: np.ndarray, price_now: float, end: int, flat_pct: float = 2.0) -> Dict:
    """At most four lines: the trend, the level above, the level below, and the one price is on."""
    trend = last_trend(bars, prices, kinds, flat_pct)
    line = _trend_line(trend, trend_candidates, end) if trend else None
    out: List[Dict] = []
    if trend:
        at_now = at_bar(line, end) if line else None
        broken = bool(line and ((trend["direction"] == DOWN and price_now > at_now)
                                or (trend["direction"] == UP and price_now < at_now)))
        out.append({"role": "the trend", "price": at_now, "direction": trend["direction"],
                    "slope": line["slope"] if line else trend["slope"],
                    "broken": broken, "line": line, "structure": trend})

    on = next((l for l in levels if abs(l["price"] / price_now - 1) * 100 <= ON_LEVEL_PCT), None)
    if on is not None:
        # named by the trend: price working down into it is resistance, working up is support
        role = "resistance" if trend and trend["direction"] == DOWN else "support"
        out.append({**on, "role": f"the level price is on ({role})"})
    for label, above in (("the level above", True), ("the level below", False)):
        lv = _nearest(levels, price_now, above)
        if lv is not None:
            out.append({**lv, "role": label})
    return {"price_now": price_now, "trend": trend, "lines": out}
