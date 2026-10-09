"""
Lines made from the zigzag he likes, and KEPT (owner, 2026-10-08: "if we dont keep what we drew
previously how are we gonna find a breakout or retest on that? the sr lines change a lot too.
remember in the zigzag how we saved and built on?" ... "i like the zigzag use that for the lines").

Measured before: of the lines on his screen, 74% were still there the next day and 47% a week later;
the trend line ended 633 times since 2018 and 446 of those times price had never crossed it.

  points   the frozen zigzag as it stood THAT day (frozen_zigzag.frozen_points) - decided on the day
           each point was confirmed, never redrawn
  levels   a line needs AT LEAST TWO zigzag points at one level (within SAME_LINE_PCT) - one point is a
           point, not a line. Shown: the most recently touched line above price and below it, decided
           only when the zigzag makes a point; price going through one is its breakout, it stays
  trend    the trend by his counted rule - it ends only when 2 higher highs AND 2 higher lows (or 2
           lower) replace it, "before that its noise" - and its line from where it began, over its own
           zigzag dots (zigzag_trend.trend_line). A close beyond the line is its breakout, not its end.
"""
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from business_logic_services.frozen_zigzag import frozen_points
from business_logic_services.setup_roster import ON_LEVEL_PCT
from modules.shapes.sr_turning_points import PEAK
from business_logic_services.zigzag_strength import compared, level_strength, trend_strength
from business_logic_services.zigzag_trend import trend_by_count, trend_line

SAME_LINE_PCT = 1.5       # a new point this close to a line touches it - the page's touch zone (his boxes +-1.4%)


def _points(df, d: int, size: float, cache: Dict):
    tp = frozen_points(df, d, size, cache)
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    return [(int(i), int(k), float(high[i] if k == PEAK else low[i]), int(c))
            for i, k, c in zip(tp["idx"], tp["kind"], tp["conf"])]


def _at(line: Dict, bar: int) -> float:
    return float(np.exp(line["y1"] + line["slope"] * (bar - line["x1"])))


def trend_lines(df: pd.DataFrame, end: int, size: float, cache: Dict) -> List[Dict]:
    """The trend's line at `end` (zigzag_trend.trend_line): the trend by his counted rule, its line from
    where it began over its own zigzag dots. It lives as long as the trend; the first close beyond it by
    more than SAME_LINE_PCT after its second dot is marked `broken` - its breakout - and it stays."""
    pts = _points(df, end, size, cache)
    line = trend_line(pts, trend_by_count(pts))
    if line is None:
        return []
    close = df["Close"].to_numpy()
    b = int(line["points"][1])
    for k in range(b + 1, end + 1):
        past = close[k] / _at(line, k) - 1 if line["down"] else 1 - close[k] / _at(line, k)
        if past * 100 > SAME_LINE_PCT:
            line["broken"] = k
            break
    return [line]


def _groups(pts) -> List[List]:
    """Zigzag points at one level, oldest first: a point joins the line it lands on (within
    SAME_LINE_PCT of the line's first point), or starts a candidate of its own."""
    groups: List[List] = []
    for p in pts:
        near = [g for g in groups if abs(np.log(g[0][2] / p[2])) * 100 <= SAME_LINE_PCT]
        if near:
            min(near, key=lambda g: abs(np.log(g[0][2] / p[2]))).append(p)
        else:
            groups.append([p])
    return groups


def levels(pts, close) -> List[Dict]:
    """The S/R lines: levels where AT LEAST TWO zigzag points sit - "why is this a resistance ... it
    touches one zigzag point. fix the lines code" (owner, 2026-10-08). One point is a point, not a line.

    Which two are shown is decided only when the zigzag makes a point ("zigzag didnt make a new point
    you dont create a new sr line"): at the close of the day the last point was confirmed, the most
    recently touched line above price and the one below. Price going through one later is a breakout
    of it - the line stays. `close`: the closes, to read the day the last point was confirmed."""
    if not pts:
        return []
    c0 = float(close[pts[-1][3]])
    lines = [g for g in _groups(pts) if len(g) >= 2]
    now = float(close[-1]) if hasattr(close, "__len__") else c0
    out = []
    for above in (True, False):
        side = [g for g in lines if (g[0][2] > c0) == above]
        if not side:
            continue
        g = max(side, key=lambda g: g[-1][0])            # the most recently touched
        price = g[0][2]
        near = abs(price / now - 1) * 100 <= ON_LEVEL_PCT
        role = "the level price is on" if near else ("resistance above" if price > now else "support below")
        kinds = {q[1] for q in g}
        out.append({"role": role, "price": price, "bar": g[0][0], "conf": g[0][3], "kind": g[0][1],
                    "touches": [q[0] for q in g], "members": g,
                    "made_by": "peaks" if kinds == {PEAK} else "valleys" if kinds == {-PEAK} else "peaks and valleys"})
    return out


def at_day(df: pd.DataFrame, end: int, size: float, cache: Dict) -> Dict:
    """The kept lines at `end`: the levels and trend lines, each with what it is made of."""
    pts = _points(df, end, size, cache)
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    trends = [{**t, "strength": trend_strength(t, pts, high, low, end)} for t in trend_lines(df, end, size, cache)]
    # the trend a level is measured against: the biggest one still standing, else the biggest broken one
    main = max(trends, key=lambda t: (t["broken"] is None, t["strength"]["size"]), default=None)
    lv = []
    for l in levels(pts, df["Close"].to_numpy()[:end + 1]):
        s = level_strength(l["members"], pts, high, low, end)
        s.update(rel=compared(s, main["strength"] if main else None),
                 trend_size=main["strength"]["size"] if main else None,
                 trend_word=(("down" if main["down"] else "up") + " trend") if main else None)
        lv.append({**l, "strength": s})
    return {"points": pts, "levels": lv, "trends": trends, "direction": direction(trends, close_now(df, end), end)}


def direction_at(df, end: int, size: float, cache: Dict) -> Dict:
    """The trend's direction at `end`, from its trend lines only."""
    return direction(trend_lines(df, end, size, cache), close_now(df, end), end)


def close_now(df, end: int) -> float:
    return float(df["Close"].iloc[end])


def direction(trends: List[Dict], close: float, end: int) -> Dict:
    """The trend and its line are one thing: the trend line exists only while the trend (his counted
    rule) lives, so its direction is the trend's - "a trend is not over with a close above its with 2
    zigzag dots that get higher and higher" (owner, 2026-10-09)."""
    line = trends[0] if trends else None
    state = ("down" if line["down"] else "up") if line else "none"
    return {"state": state, "down": line if line and line["down"] else None, "up": line if line and not line["down"] else None}
