"""
Events over history, each judged against the lines of its own day (line_history) - the layer above
the lines and below the strategies (owner, 2026-10-08: "make sure its well separated so we could
choose the specific breakout pattern or patterns with flags and assemble full strategies").

  line events     breakout, fakeout, sweep, retest, bounce at each line shown that day
                  (modules/events/detectors.py)
  trend_change    the day the trend's direction changes (the concept's trend switch)
  patterns        double top / bottom, head and shoulders, cup and handle, flags
                  (modules/patterns/)
  candle          optional: keep only events whose candle (or the one before) is a pattern the
                  event's way (modules/candlesticks/candle_signals.py)
  confluence      every line event says which OTHER lines were in its zone that day

Every switch is in EventFlags; every event carries what decided it (event_story says it in words).
"""
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple
import json
import numpy as np
import pandas as pd
from business_logic_services.event_story import why
from business_logic_services.line_concepts import Concepts
from business_logic_services.line_history import line_history, value_at
from modules.candlesticks.candle_signals import PATTERNS as CANDLES, candle_masks
from modules.events.detectors import DETECTORS
from modules.patterns.pattern_scan import PATTERN_TYPES, scan_patterns

LINE_EVENTS = tuple(DETECTORS)


@dataclass(frozen=True)
class EventFlags:
    types: Tuple[str, ...] = ("breakout", "fakeout", "sweep", "retest", "bounce", "trend_change")
    patterns: Tuple[str, ...] = PATTERN_TYPES
    closes: int = 1                  # breakout: closes in a row beyond the zone (Murphy's 2-day rule = 2)
    fakeout_within: int = 5          # bars to close back after a close beyond
    retest_within: int = 20          # bars after a breakout to come back to the line
    candle: str = "off"              # off | pin | engulfing | piercing | any


def _zone(line: Dict, half: float):
    if line["kind"] == "level":
        lo, hi = min(line["low"], line["price"] * (1 - half)), max(line["high"], line["price"] * (1 + half))
        return lambda bar: (lo, hi)
    return lambda bar: (value_at(line, bar) * (1 - half), value_at(line, bar) * (1 + half))


def _params(kind: str, f: EventFlags) -> Dict:
    return {"breakout": {"closes": f.closes}, "fakeout": {"within": f.fakeout_within},
            "retest": {"within": f.retest_within, "closes": f.closes}}.get(kind, {})


def _line_events(day: Dict, d: int, px, f: EventFlags) -> List[Dict]:
    half = day["band_pct"] / 200
    lines = day["levels"] + [t for t in day["trends"] if not t["far"]]
    out = []
    for line in lines:
        zone = _zone(line, half)
        for kind in (k for k in f.types if k in DETECTORS):
            ev = DETECTORS[kind](*px, zone, d, **_params(kind, f))
            if ev is None:
                continue
            lo, hi = zone(d)
            near = [o["id"] for o in lines if o is not line and lo <= value_at(o, d) <= hi]
            out.append({**ev, "line": {**line, "value": value_at(line, d), "zone": [lo, hi]},
                        "confluence": near})
    return out


def _new(ev: Dict, kept: List[Dict], band_pct: float) -> bool:
    """The same event on nearly the same line a few days later is the same event."""
    for k in reversed(kept[-20:]):
        if (k["type"] == ev["type"] and k["direction"] == ev["direction"] and ev["bar"] - k["bar"] <= 5
                and "line" in k and abs(np.log(k["line"]["value"] / ev["line"]["value"])) * 100 <= band_pct):
            return False
    return True


def _trend_change(prev: Dict, day: Dict, d: int):
    now = next((t for t in day["trends"] if not t["previous"]), None)
    was = next((t for t in prev["trends"] if not t["previous"]), None)
    if now is None or was is None or now["direction"] == was["direction"]:
        return None
    return {"type": "trend_change", "direction": now["direction"], "bar": d, "from_bar": d,
            "was": was["direction"], "line": {**now, "value": value_at(now, d)}, "confluence": []}


def _confirm(ev: Dict, masks: Dict, which: str) -> Dict:
    names = CANDLES if which == "any" else (which,)
    hit = [n for n in names for b in (ev["bar"], ev["bar"] - 1) if masks[n][ev["direction"]][b]]
    return {**ev, "candle": hit[0]} if hit else None


def compute_events(df: pd.DataFrame, c: Concepts, size: float, f: EventFlags, cache: Dict) -> List[Dict]:
    key = ("events", json.dumps([asdict(c), asdict(f), size, len(df)], sort_keys=True))
    if key in cache:
        return cache[key]
    hist = line_history(df, c, size, cache)
    px = tuple(df[k].to_numpy() for k in ("Close", "High", "Low"))
    days = sorted(hist)
    out: List[Dict] = []
    for prev_d, d in zip(days, days[1:]):
        day = hist[d]
        for ev in _line_events(day, d, px, f):
            if _new(ev, out, day["band_pct"]):
                out.append(ev)
        if "trend_change" in f.types:
            ev = _trend_change(hist[prev_d], day, d)
            if ev:
                out.append(ev)
    out += scan_patterns(df, c.swings, size, {d: hist[d]["band_pct"] for d in days}, f.patterns, cache)
    if f.candle != "off":
        masks = candle_masks(df)
        out = [e for e in (_confirm(e, masks, f.candle) for e in out) if e]
    out = sorted(out, key=lambda e: (e["bar"], e["type"]))
    t = df.index
    out = [{**e, "date": t[e["bar"]].strftime("%Y-%m-%d"), "time": int(t[e["bar"]].timestamp()),
            "from_time": int(t[e["from_bar"]].timestamp()), "why": why(e, t), **_drawn(e, t)} for e in out]
    cache[key] = out
    return out


def _drawn(e: Dict, t: pd.DatetimeIndex) -> Dict:
    """What the page draws for an event: the line it happened at (a little before and after) or
    the pattern's points and neckline - as (time, price) pairs."""
    pt = lambda b, line: {"time": int(t[b].timestamp()), "price": value_at(line, b)}
    last = len(t) - 1
    if "neckline" in e:
        neck = e["neckline"]
        return {"shape": [{"time": int(t[b].timestamp()), "price": p} for b, p in e["points"]],
                "line_points": [pt(e["points"][0][0], neck), pt(e["bar"], neck)]}
    a, b = max(0, e["from_bar"] - 30), min(last, e["bar"] + 10)
    return {"line_points": [pt(a, e["line"]), pt(b, e["line"])]}
