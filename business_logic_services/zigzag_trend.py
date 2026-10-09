"""
The trend by HIS counted rule, on the zigzag as it stood that day (owner, 2026-10-07: "up trend is 2
higher highs and 2 higher lows. downtrend is the opposite. there is no trend change if not at least 2
such"; at 2023-03-24: "two higher highs but not two higher lows only one and than a lower low but not
another lower low after that so no change to downtrend").

Walked point by point:
  - every peak is compared with the peak before it, every valley with the valley before it; within
    SAME_PCT it is "the same" and counts for nothing
  - against the trend we are in, higher highs and higher lows (or lower ones) are COUNTED since the
    trend's last extreme; 2 of each change the trend
  - a new extreme the trend's way (a lower low in a down trend) is the trend going on: the counts start
    again from there - so one small bounce never adds up with another one months later
"""
import math
from typing import Dict, List
from modules.shapes.sr_turning_points import PEAK

SAME_PCT = 1.5           # two peaks this close are at one level - the lines' touch zone


def _step(a: float, b: float) -> int:
    if abs(b / a - 1) * 100 <= SAME_PCT:
        return 0
    return 1 if b > a else -1


def trend_by_count(pts: List) -> Dict:
    """`pts`: the zigzag's points known that day, (bar, kind, price, confirmed), oldest first.
    `start`: where the trend began - its extreme (the highest peak for a down trend) since the trend
    before it was confirmed."""
    state, since, extreme, start, flip = None, None, None, None, 0
    count = {"hh": 0, "hl": 0, "lh": 0, "ll": 0}
    last = {PEAK: None, -PEAK: None}
    for p in pts:
        k, price = p[1], p[2]
        prev = last[k]
        last[k] = p
        if prev is None:
            continue
        s = _step(prev[2], price)
        if k == PEAK:
            count["hh"] += s > 0; count["lh"] += s < 0
        else:
            count["hl"] += s > 0; count["ll"] += s < 0
        if state == "down" and k != PEAK and (extreme is None or price < extreme):
            extreme = price; count = dict.fromkeys(count, 0)              # the down trend going on
        elif state == "up" and k == PEAK and (extreme is None or price > extreme):
            extreme = price; count = dict.fromkeys(count, 0)              # the up trend going on
        if state != "up" and count["hh"] >= 2 and count["hl"] >= 2:
            seg = [q for q in pts[flip:pts.index(p) + 1] if q[1] != PEAK]
            state, since, extreme = "up", p, price; count = dict.fromkeys(count, 0)
            start, flip = min(seg, key=lambda q: q[2]), pts.index(p)
        elif state != "down" and count["lh"] >= 2 and count["ll"] >= 2:
            seg = [q for q in pts[flip:pts.index(p) + 1] if q[1] == PEAK]
            state, since, extreme = "down", p, price; count = dict.fromkeys(count, 0)
            start, flip = max(seg, key=lambda q: q[2]), pts.index(p)
    against = ("hh", "hl") if state == "down" else ("lh", "ll") if state == "up" else ()
    return {"state": state or "none", "since": since, "start": start, "count": {k: count[k] for k in against}}


def trend_line(pts: List, t: Dict) -> Dict:
    """The trend's line, on its own zigzag dots (owner, 2026-10-09: "even the trends you did draw are bad
    and dont rely on 2 dots"): over the peaks of a down trend (under the valleys of an up one) FROM WHERE
    IT BEGAN (his: "the line runs over the highs ... from where the trend began") - through the one of its
    later dots that makes it touch the most of them (within SAME_PCT); fewer
    dots poking through it breaks a tie. It is the trend's line for as long as the trend lives: a close
    beyond it is a breakout, not the end - "a trend is not over with a close above its with 2 zigzag dots
    that get higher and higher. not same height. before that its noise"."""
    if t["state"] not in ("up", "down") or t["start"] is None:
        return None
    down = t["state"] == "down"
    side = [p for p in pts if p[1] == (PEAK if down else -PEAK) and p[0] >= t["start"][0]]
    if len(side) < 2:
        return None
    best = None
    for i, a in enumerate(side[:1]):               # from where the trend began: its first dot is the start
        for b in side[i + 1:]:
            slope = (math.log(b[2]) - math.log(a[2])) / max(b[0] - a[0], 1)
            if (slope > 0) == down:
                continue                          # a down trend's line falls, an up trend's rises
            at = lambda q: math.exp(math.log(a[2]) + slope * (q[0] - a[0]))
            touch = sum(abs(q[2] / at(q) - 1) * 100 <= SAME_PCT for q in side)
            poke = sum((q[2] / at(q) - 1) * 100 > SAME_PCT if down else (1 - q[2] / at(q)) * 100 > SAME_PCT for q in side)
            key = (-poke, touch, -a[0])               # over the highs first, then the most dots on it
            if best is None or key > best[0]:
                best = (key, a, b, slope, touch)
    if best is None:
        return None
    _, a, b, slope, touch = best
    return {"down": down, "x1": float(a[0]), "y1": float(math.log(a[2])), "slope": float(slope),
            "points": [a[0], b[0]], "prices": [a[2], b[2]], "born": int(t["since"][3]), "touches_n": touch,
            "start": t["start"], "broken": None}


def trend_words(t: Dict, day) -> str:
    if t["state"] == "none":
        return "no trend yet by the rule (2 higher highs and 2 higher lows, or 2 lower)"
    s, c = t["since"], t["count"]
    names = {"hh": "higher highs", "hl": "higher lows", "lh": "lower highs", "ll": "lower lows"}
    against = ", ".join(f"{names[k]} {v}/2" for k, v in c.items())
    return f"{'an UP' if t['state'] == 'up' else 'a DOWN'} trend since {day(s[0])} ({s[2]:,.0f}); against it so far: {against}"
