"""
Events at ONE line, decided on day `d` from bars <= d only (owner, 2026-09-23: events are "defined
by a MOVE, not one candle"; 2026-10-08: "the events and how you decided them").

A line is given as `zone(bar) -> (lo, hi)`: the band around it at that bar. Price is ABOVE the zone,
INSIDE it or BELOW it, judged on the CLOSE (Murphy: a close beyond counts, a wick does not).

  breakout  the `closes`-th close in a row beyond the zone, coming from the other side
  fakeout   price closed beyond the zone and within `within` bars closed back on the side it came
            from (Wyckoff's spring / upthrust; Raschke's Turtle Soup trades it)
  sweep     one candle's wick through the zone, closing back on its side (SMC; his tail)
  retest    after a breakout, the first return into the zone that closes on the breakout side
  bounce    price came into the zone from one side and its first close out of it is on that side

Each returns None or {type, direction, bar (decided), from_bar (where its move began), ...numbers}.
`direction` is where the event points price: a breakout up is "up", a fake breakout up is "down".
"""
from typing import Callable, Dict, Optional, Tuple
import numpy as np

ABOVE, INSIDE, BELOW = 1, 0, -1
Zone = Callable[[int], Tuple[float, float]]
WORD = {ABOVE: "up", BELOW: "down"}


def side(price: float, zone: Zone, bar: int) -> int:
    lo, hi = zone(bar)
    return ABOVE if price > hi else BELOW if price < lo else INSIDE


def _came_from(close, zone: Zone, j: int, lookback: int) -> Tuple[int, int]:
    """Walking back from bar j over closes inside the zone: the side price was on before, and the
    first bar of the stretch that ended at j."""
    stop = max(0, j - lookback)
    while j > stop and side(close[j], zone, j) == INSIDE:
        j -= 1
    return side(close[j], zone, j), j + 1


def breakout(close, high, low, zone: Zone, d: int, closes: int = 1, lookback: int = 60) -> Optional[Dict]:
    s = side(close[d], zone, d)
    if s == INSIDE or d - closes < 0:
        return None
    if any(side(close[d - k], zone, d - k) != s for k in range(closes)):
        return None
    if side(close[d - closes], zone, d - closes) == s:
        return None                                  # already beyond before: not decided today
    before, start = _came_from(close, zone, d - closes, lookback)
    if before != -s:
        return None                                  # came out of the zone on its own side
    lo, hi = zone(d)
    beyond = (close[d] / hi - 1) if s == ABOVE else (1 - close[d] / lo)
    return {"type": "breakout", "direction": WORD[s], "bar": d, "from_bar": start,
            "closes": closes, "beyond_pct": float(beyond * 100)}


def fakeout(close, high, low, zone: Zone, d: int, within: int = 5) -> Optional[Dict]:
    """Back on the original side of the LINE (its middle) today, for the first time since it CLOSED
    beyond the zone."""
    lo, hi = zone(d)
    mid = (lo + hi) / 2
    for s0 in (BELOW, ABOVE):                        # the side it came from
        back = close[d] < mid if s0 == BELOW else close[d] > mid
        was_out = (close[d - 1] >= mid) if s0 == BELOW else (close[d - 1] <= mid)
        if not (back and was_out):
            continue
        for j in range(d - 1, max(0, d - within) - 1, -1):
            jlo, jhi = zone(j)
            poke = close[j] > jhi if s0 == BELOW else close[j] < jlo
            if poke:
                before, _ = _came_from(close, zone, j - 1, within * 4)
                if before == s0:
                    far = (max(high[j:d]) / jhi - 1) if s0 == BELOW else (1 - min(low[j:d]) / jlo)
                    return {"type": "fakeout", "direction": WORD[s0], "bar": d,
                            "from_bar": j, "beyond_pct": float(far * 100), "bars_out": d - j}
            back_before = close[j] < (jlo + jhi) / 2 if s0 == BELOW else close[j] > (jlo + jhi) / 2
            if back_before:
                break                                # an earlier return: this one is not the first
    return None


def sweep(close, high, low, zone: Zone, d: int) -> Optional[Dict]:
    """One candle whose wick goes through the zone and closes back on the side it came from - his
    tail ("broke the support in a tail but got back and i ignored this spike"; SMC's sweep)."""
    lo, hi = zone(d)
    came = side(close[d - 1], zone, d - 1)
    if came == BELOW and high[d] > hi and close[d] < (lo + hi) / 2:
        return {"type": "sweep", "direction": "down", "bar": d, "from_bar": d,
                "beyond_pct": float((high[d] / hi - 1) * 100)}
    if came == ABOVE and low[d] < lo and close[d] > (lo + hi) / 2:
        return {"type": "sweep", "direction": "up", "bar": d, "from_bar": d,
                "beyond_pct": float((1 - low[d] / lo) * 100)}
    return None


def retest(close, high, low, zone: Zone, d: int, within: int = 20, closes: int = 1) -> Optional[Dict]:
    lo, hi = zone(d)
    for b in range(d - 1, max(1, d - within) - 1, -1):
        brk = breakout(close, high, low, zone, b, closes)
        if brk is None:
            continue
        up = brk["direction"] == "up"
        touched = (lambda k: low[k] <= zone(k)[1]) if up else (lambda k: high[k] >= zone(k)[0])
        if not touched(d) or any(touched(k) for k in range(b + 1, d)):
            return None                              # not back today, or not the first time back
        holds = close[d] > (lo + hi) / 2 if up else close[d] < (lo + hi) / 2
        if not holds:
            return None
        return {"type": "retest", "direction": brk["direction"], "bar": d, "from_bar": b,
                "breakout_bar": b, "bars_after": d - b}
    return None


def bounce(close, high, low, zone: Zone, d: int, within: int = 20) -> Optional[Dict]:
    s = side(close[d], zone, d)
    if s == INSIDE or side(close[d - 1], zone, d - 1) == s:
        return None
    touches = lambda k: low[k] <= zone(k)[1] and high[k] >= zone(k)[0]
    j = d - 1
    while j > max(0, d - within) and (touches(j) or side(close[j], zone, j) == INSIDE):
        if side(close[j], zone, j) == -s:
            return None                              # closed on the far side: that is not a turn
        j -= 1
    if j == d - 1 and not touches(d - 1) and not touches(d):
        return None
    if side(close[j], zone, j) != s:
        return None                                  # it came from the other side: a breakout
    return {"type": "bounce", "direction": WORD[s], "bar": d, "from_bar": j + 1, "bars_in": d - j - 1}


DETECTORS = {"breakout": breakout, "fakeout": fakeout, "sweep": sweep, "retest": retest, "bounce": bounce}
