"""
The lines, built from concepts he can switch on and off (owner, 2026-10-08: "implementing these
concepts with flags will help in testing it ... its all variables that definitely work together but
also independently"). The same flags will feed the backtest.

  swings  where peaks and valleys come from: zigzag (ours, frozen) | pivots | atr
  group   channels: points within the band are ONE level (S/R Channels) | off: every point a level
  band    how wide a level may be: move (a share of the move, ours) | range (5% of 300 bars, the script)
  parts   what strength is made of (level_parts)
  trend   protected1 | protected2 (breaks of the protected low) | window (the rule before) | off
  pick    which lines are shown: roster (his rules) | nearest | strongest, per_side each way

Every kept line carries what made it - its points, its band, its score and its parts, and the rule
that kept it - and the card says it (concept_story).
"""
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from business_logic_services.concept_story import concept_story
from business_logic_services.frozen_zigzag import frozen_points
from business_logic_services.level_parts import level_parts
from business_logic_services.level_strength import add_strength
from business_logic_services.line_rules import MOVE_BAND
from business_logic_services.setup_roster import ON_LEVEL_PCT, _reach, keep_roster
from business_logic_services.swing_frame import swing_frame
from business_logic_services.trend_state import DOWN, UP, flat_for
from business_logic_services.trend_structure import read_structure
from modules.shapes.sr_channels import group_channels, non_overlapping, range_width
from modules.shapes.sr_turning_points import PEAK
from modules.shapes.swing_sources import swing_points

BREAKS = {"protected1": 1, "protected2": 2, "window": 0}


@dataclass(frozen=True)
class Concepts:
    swings: str = "zigzag"
    group: str = "channels"
    band: str = "move"
    parts: Tuple[str, ...] = ("pivots", "bars", "sweeps")
    trend: str = "protected1"
    pick: str = "roster"
    per_side: int = 1


def _points(df, end, c: Concepts, size: float, cache) -> Dict:
    tp = frozen_points(df, end, size, cache) if c.swings == "zigzag" else swing_points(df, c.swings, size, cache)
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    return {k: v[known] for k, v in tp.items()}


def _level(ch: Dict, high, low, close, end: int, c: Concepts, tp: Dict, yard: float) -> Dict:
    """A channel as a level the roster and the page read, with what it is made of."""
    bars = sorted({b for b, _ in ch["members"]})
    prices = [p for _, p in ch["members"]]
    mid = float(np.exp(np.mean(np.log(prices))))
    lv = {"price": mid, "high": ch["hi"], "low": ch["lo"], "y": float(np.log(mid)),
          "points": [float(b) for b in bars], "point_prices": prices, "touches": len(bars),
          "visits": len(bars), "history": 0, "anchor": float(bars[-1]), "merged_from": len(bars),
          "from_history": False, "first": float(bars[0]), "last": float(bars[-1]), "at_price_now": False}
    measured = add_strength([lv], tp, high, low, end, yard)[0]["strength"] if "measured" in c.parts else 0.0
    return {**lv, **level_parts(ch, high, low, close, end, c.parts, measured)}


def _pick(levels: List[Dict], trend, f, c: Concepts, yard: float, band_pct: float, end: int):
    """Which lines are shown, and in words why each was kept."""
    if c.pick == "roster":
        kept, trends = keep_roster(levels, [], f.bars, f.prices, f.kinds, f.price_now, end, flat_for(yard),
                                   trend=trend, turned_at=f.turned_at(), band_pct=band_pct,
                                   move_pct=yard, move_from_bar=f.now_from_bar, min_visits=2)
        return [{**l, "kept_by": "his roster"} for l in kept], trends
    on = [l for l in levels if l["low"] * (1 - ON_LEVEL_PCT / 100) <= f.price_now <= l["high"] * (1 + ON_LEVEL_PCT / 100)]
    rest = [l for l in levels if l not in on]
    key = (lambda l: -l["score"]) if c.pick == "strongest" else (lambda l: abs(np.log(l["price"] / f.price_now)))
    above = sorted([l for l in rest if l["price"] > f.price_now], key=key)[:c.per_side]
    below = sorted([l for l in rest if l["price"] < f.price_now], key=key)[:c.per_side]
    why = f"{c.pick} {c.per_side} each side"
    kept = [{**l, "on": True, "kept_by": "price is on it"} for l in on[:1]] + \
           [{**l, "kept_by": why} for l in above + below]
    if trend is None:
        return kept, []
    shown = trend.get("previous") if trend.get("inside") else trend
    ok = shown is not None and shown.get("direction") in (UP, DOWN)
    return kept, [_reach(shown, f.price_now, end, yard)] if ok else []


def concept_lines(df: pd.DataFrame, end: int, c: Concepts, size: float, cache: Dict) -> Dict:
    high, low, close = (df[k].to_numpy() for k in ("High", "Low", "Close"))
    f = swing_frame(df, end, size, cache)
    trend, yard = (read_structure(df, end, f.now_move, size, cache, breaks=BREAKS[c.trend])
                   if c.trend in BREAKS and f.now_move > 0 else (None, f.now_move))
    tp = _points(df, end, c, size, cache)
    pts = [(int(i), float(high[i] if k == PEAK else low[i])) for i, k in zip(tp["idx"], tp["kind"])]
    width = (f.price_now * yard * MOVE_BAND / 100 if c.band == "move" else range_width(high, low, end))
    chans = (group_channels(pts, width) if c.group == "channels"
             else [{"lo": p, "hi": p, "members": [(b, p)]} for b, p in pts])
    # the strongest of overlapping channels wins; "measured" is added after, on the few left
    base = Concepts(**{**asdict(c), "parts": tuple(p for p in c.parts if p != "measured")})
    for ch in chans:
        ch["score"] = level_parts(ch, high, low, close, end, base.parts)["score"]
    chans = non_overlapping(chans, lambda ch: ch["score"] + len(ch["members"]) / 1000, len(chans))
    levels = [_level(ch, high, low, close, end, c, tp, yard) for ch in chans]
    band_pct = width / f.price_now * 100
    kept, trends = _pick(levels, trend, f, c, yard, band_pct, end)
    if c.trend == "off":
        trends = []                     # the roster falls back to a trend of its own otherwise
    # a level the roster made itself (a range wall, an up trend's latest peak) is scored the same way
    kept = [l if "score" in l else
            {**_level({"lo": l["low"], "hi": l["high"], "members": list(zip(l["points"], l["point_prices"]))},
                      high, low, close, end, c, tp, yard),
             **{k: l[k] for k in ("kept_by", "wall", "on") if k in l}}
            for l in kept]
    dots = [{"bar": b, "time": int(df.index[b].timestamp()), "price": p,
             "kind": "peak" if k == PEAK else "valley"} for (b, p), k in zip(pts, tp["kind"])]
    return {"levels": kept, "trends": trends, "points": dots, "concepts": asdict(c),
            "band_pct": band_pct, "move_pct": yard,
            "story": concept_story(df, end, f, kept, trends, c, yard, band_pct)}
