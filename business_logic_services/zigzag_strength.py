"""
What each zigzag line is worth - the same measures for a level and a trend line, from the zigzag's own
points (owner, 2026-10-08: "add strengths of everything. from dots to lines to sizes to touches to
duration"; 2026-10-09: "in its explanation i wanna see its size and slope and duration and touches and
score").

  a dot      its swing: the move into it and out of it (to the next point, or as far as price has got)
  a line     touches   the zigzag points on it (a level: within SAME_PCT of its price; a trend line:
                       within SAME_PCT of the line at their bar), with their dates
             size      a level: its biggest touch's swing; a trend line: the move it carried, from its
                       first point to the furthest price before it broke (or today)
             slope     %/day (a level: 0)
             duration  days from its first touch to its last (a trend line: to its break, or today)
             score     the total % price turned at it - the sum of its touches' swings: three big
                       turns score high, one small touch low
             age, last touch, and - for a level - its size as a share of the trend's
"""
from typing import Dict, List, Optional
import numpy as np
from modules.shapes.sr_turning_points import PEAK

SAME_PCT = 1.5            # a point this close to a line touches it - the lines' own touch zone


def _pct(a: float, b: float) -> float:
    return abs(b / a - 1) * 100


def dot_swing(pts: List, i: int, high, low, end: int) -> float:
    """The bigger of the move into point i and the move out of it, in %."""
    p = pts[i]
    into = _pct(pts[i - 1][2], p[2]) if i > 0 else 0.0
    if i + 1 < len(pts):
        out = _pct(p[2], pts[i + 1][2])
    else:                                   # the leg out is still running: as far as it has got
        seg = slice(p[0] + 1, end + 1)
        out = _pct(p[2], (low[seg].min() if p[1] == PEAK else high[seg].max())) if p[0] < end else 0.0
    return max(into, out)


def _measure(touch_pts: List, pts: List, high, low, end: int) -> Dict:
    index = {p[0]: i for i, p in enumerate(pts)}
    swings = [dot_swing(pts, index[p[0]], high, low, end) for p in touch_pts if p[0] in index]
    first, last = touch_pts[0][0], touch_pts[-1][0]
    return {"touches": len(touch_pts), "points": [int(p[0]) for p in touch_pts], "swings": swings,
            "score": float(sum(swings)), "first": int(first), "last_touch": int(last), "age_days": int(end - first)}


def level_strength(members: List, pts: List, high, low, end: int) -> Dict:
    m = _measure(members, pts, high, low, end)
    return {**m, "size": max(m["swings"], default=0.0), "slope": 0.0, "duration": int(m["last_touch"] - m["first"])}


def trend_strength(line: Dict, pts: List, high, low, end: int) -> Dict:
    a = int(line["points"][0])
    stop = int(line["broken"]) if line.get("broken") is not None else end
    seg = slice(a, stop + 1)
    far = low[seg].min() if line["down"] else high[seg].max()
    at = lambda bar: float(np.exp(line["y1"] + line["slope"] * (bar - line["x1"])))
    kind = PEAK if line["down"] else -PEAK
    on = [p for p in pts if p[1] == kind and a <= p[0] <= stop and _pct(at(p[0]), p[2]) <= SAME_PCT]
    m = _measure(on or [p for p in pts if p[0] in line["points"]], pts, high, low, end)
    return {**m, "size": _pct(line["prices"][0], far), "slope": float(np.expm1(line["slope"]) * 100),
            "duration": int(stop - a)}


def compared(level: Dict, trend: Optional[Dict]) -> Optional[float]:
    """The level's size as a share of the trend's: 0.1 = the trend is ten times bigger."""
    if not trend or trend["size"] <= 0:
        return None
    return level["size"] / trend["size"]


def words(s: Dict, kind: str, day, price_now: float, value_now: float, broken: Optional[int] = None) -> str:
    """The line's card, in one format for levels and trend lines."""
    touches = ", ".join(day(b) for b in s["points"])
    swings = " + ".join(f"{x:.1f}%" for x in s["swings"])
    where = value_now / price_now - 1
    vs = (f", {s['rel']:.2f}x the {s['trend_word']}'s {s['trend_size']:.0f}%" if s.get("rel") is not None else "")
    size = (f"Size {s['size']:.1f}% (its biggest turn{vs})" if kind == "level"
            else f"Size {s['size']:.0f}% (the move it carried)")
    return (f"{size} · slope {s['slope']:+.2f}%/day · duration {s['duration']} days · {s['touches']} touches "
            f"({touches}) · score {s['score']:.0f} (price turned {swings} at it) · {s['age_days']} days old, last touch "
            f"{day(s['last_touch'])} · {abs(where) * 100:.1f}% {'above' if where > 0 else 'below'} price · "
            + (f"broken {day(broken)}." if broken is not None else "not broken."))
