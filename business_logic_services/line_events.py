"""
What happened at the lines on the screen, during the move running now - the events that matter for
a trade, as stars on those lines (owner, 2026-10-08: "just for the support and resistance and trend
lines show a breakout or retest or whatever is important for trades. currently i see a million
dots ... lets think more simply about whats related to the current price and current lines").

Checked before: of 20 events at his 2025-12-28 screen, 5 made sense - breakouts and retests of lines
that had stood for weeks - while 8 were chop on lines a few days old, two labels on one candle.
So: only today's lines, only breakout / retest / fakeout, only since the move running now began, one
event per candle and line. The zone is the touch zone the page draws on the lines (his drawn boxes,
+-1.4%). The detectors are the same as the events layer's (modules/events/detectors.py).
"""
from typing import Dict, List
import numpy as np
import pandas as pd
from business_logic_services.event_story import why
from modules.events.detectors import breakout, fakeout, retest

TYPES = (("breakout", breakout), ("retest", retest), ("fakeout", fakeout))   # first wins on one candle


def _line(l: Dict, end: int) -> Dict:
    """A setup-card line as the detectors read it: a level is flat, a trend keeps its slope."""
    if l.get("slope_pct_day") is None:
        return {"kind": "level", "price": l["price"], "low": l["price"], "high": l["price"], "role": l["role"]}
    return {"kind": "trend", "x1": float(end), "y1": float(np.log(l["price"])),
            "slope": float(np.log1p(l["slope_pct_day"] / 100)), "role": l["role"]}


def _at(line: Dict, bar: int) -> float:
    return line["price"] if line["kind"] == "level" else float(np.exp(line["y1"] + line["slope"] * (bar - line["x1"])))


def line_events(df: pd.DataFrame, end: int, story: Dict, touch_pct: float = 1.4) -> List[Dict]:
    lines = story.get("lines") or []
    if not lines or not story.get("move_from"):
        return []
    start = int(df.index.searchsorted(pd.Timestamp(story["move_from"], tz="UTC")))
    px = tuple(df[k].to_numpy() for k in ("Close", "High", "Low"))
    half, t = touch_pct / 100, df.index
    out = []
    for l in lines:
        line = _line(l, end)
        zone = lambda bar, ln=line: (_at(ln, bar) * (1 - half), _at(ln, bar) * (1 + half))
        for d in range(max(start, 1), end + 1):
            for _, detect in TYPES:
                ev = detect(*px, zone, d)
                if ev is None:
                    continue
                ev = {**ev, "line": {**line, "value": _at(line, d), "zone": list(zone(d))}, "confluence": []}
                out.append({**ev, "role": l["role"], "date": t[d].strftime("%Y-%m-%d"), "time": int(t[d].timestamp()),
                            "price": _at(line, d), "why": why(ev, t)})
                break                                  # one event per candle and line
    return sorted(out, key=lambda e: e["bar"])
