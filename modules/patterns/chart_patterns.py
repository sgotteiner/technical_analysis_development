"""
Chart patterns from the peaks and valleys known on day `d`, decided on the FIRST close through their
neckline (Edwards & Magee, Bulkowski; owner, 2026-10-08: "we dont have patterns for flags and cups
and crowns at all ... at the end of the day its sr lines"). A pattern is peaks, valleys and a line;
its completion is a breakout of that line.

  double top / bottom       two peaks (valleys) at one level; neckline: the valley (peak) between
  head and shoulders        three peaks, the middle one higher by more than "the same level", the
  (and inverse)             outer two at one level; neckline through the two valleys between them
  cup and handle            two peaks at one level with a valley deeper than the band between;
                            the handle - the pullback after the right rim - stays in the upper half
                            of the cup (O'Neil); neckline: the right rim
"The same level" is `same_pct`, the band of the day (a share of the move), never a fixed %.

Each returns None or {type, direction, bar, points: [(bar, price)], neckline: line, target}.
`target` is the measured move: the pattern's height projected from the neckline.
"""
from typing import Dict, List, Optional, Tuple
import numpy as np

Point = Tuple[int, float, int]           # (bar, price, kind) - kind +1 peak, -1 valley


def _same(a: float, b: float, pct: float) -> bool:
    return abs(a / b - 1) * 100 <= pct


def _flat(price: float) -> Dict:
    return {"kind": "level", "price": price, "low": price, "high": price}


def _through(a: Tuple[int, float], b: Tuple[int, float]) -> Dict:
    slope = (np.log(b[1]) - np.log(a[1])) / max(b[0] - a[0], 1)
    return {"kind": "trend", "x1": float(a[0]), "y1": float(np.log(a[1])), "slope": float(slope)}


def _at(line: Dict, bar: int) -> float:
    return line["price"] if line["kind"] == "level" else float(np.exp(line["y1"] + line["slope"] * (bar - line["x1"])))


def _first_cross(close, line: Dict, since: int, d: int, down: bool) -> bool:
    """Is day d the first close through the line since bar `since`?"""
    past = lambda k: close[k] < _at(line, k) if down else close[k] > _at(line, k)
    return past(d) and not any(past(k) for k in range(since + 1, d))


def _last(pts: List[Point], kind: int, n: int) -> List[Point]:
    return [p for p in pts if p[2] == kind][-n:]


def _between(pts: List[Point], a: int, b: int, kind: int) -> Optional[Point]:
    inside = [p for p in pts if a < p[0] < b and p[2] == kind]
    return (max if kind > 0 else min)(inside, key=lambda p: p[1]) if inside else None


def double(pts: List[Point], close, d: int, same_pct: float, top: bool) -> Optional[Dict]:
    k = 1 if top else -1
    two = _last(pts, k, 2)
    if len(two) < 2 or not _same(two[0][1], two[1][1], same_pct):
        return None
    mid = _between(pts, two[0][0], two[1][0], -k)
    if mid is None:
        return None
    neck = _flat(mid[1])
    if not _first_cross(close, neck, two[1][0], d, down=top):
        return None
    height = max(two[0][1], two[1][1]) - mid[1] if top else mid[1] - min(two[0][1], two[1][1])
    return {"type": "double_top" if top else "double_bottom", "direction": "down" if top else "up",
            "bar": d, "points": [two[0][:2], mid[:2], two[1][:2]], "neckline": neck,
            "target": float(mid[1] - height if top else mid[1] + height)}


def head_shoulders(pts: List[Point], close, d: int, same_pct: float, top: bool) -> Optional[Dict]:
    k = 1 if top else -1
    three = _last(pts, k, 3)
    if len(three) < 3:
        return None
    (a, pa, _), (b, pb, _), (c, pc, _) = three
    higher = (lambda x, y: x / y - 1 > same_pct / 100) if top else (lambda x, y: 1 - x / y > same_pct / 100)
    if not (higher(pb, pa) and higher(pb, pc) and _same(pa, pc, same_pct)):
        return None
    v1, v2 = _between(pts, a, b, -k), _between(pts, b, c, -k)
    if v1 is None or v2 is None:
        return None
    neck = _through(v1[:2], v2[:2])
    if not _first_cross(close, neck, c, d, down=top):
        return None
    at_head = _at(neck, b)
    return {"type": "head_shoulders" if top else "inverse_head_shoulders", "direction": "down" if top else "up",
            "bar": d, "points": [(a, pa), v1[:2], (b, pb), v2[:2], (c, pc)], "neckline": neck,
            "target": float(_at(neck, d) - (pb - at_head) if top else _at(neck, d) + (at_head - pb))}


def cup_handle(pts: List[Point], close, low, d: int, same_pct: float) -> Optional[Dict]:
    rims = _last(pts, 1, 2)
    if len(rims) < 2 or not _same(rims[0][1], rims[1][1], same_pct):
        return None
    bottom = _between(pts, rims[0][0], rims[1][0], -1)
    depth = rims[1][1] - bottom[1] if bottom else 0.0
    if bottom is None or depth / rims[1][1] * 100 <= same_pct:
        return None                                  # a dip within the band is no cup
    handle = float(np.min(low[rims[1][0]:d + 1]))
    if rims[1][1] - handle > depth / 2:
        return None                                  # the handle fell into the lower half
    neck = _flat(rims[1][1])
    if not _first_cross(close, neck, rims[1][0], d, down=False):
        return None
    return {"type": "cup_handle", "direction": "up", "bar": d,
            "points": [rims[0][:2], bottom[:2], rims[1][:2]], "neckline": neck,
            "target": float(rims[1][1] + depth), "handle_low": handle}
