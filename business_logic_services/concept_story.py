"""
The card for the concept lines: every line with what made it (owner, 2026-10-08: "i wanna know what
made the algorithm draw each line. which peaks and valleys it used, scores, whatever").

Same shape as setup_story's card, so the page's card, its click-to-focus and its touch boxes work
unchanged: role, price, kind, how, points, dates, times, zones.
"""
from typing import Dict, List
import numpy as np
from business_logic_services.level_parts import parts_text
from business_logic_services.line_rules import MOVE_BAND
from business_logic_services.trend_state import at_bar
from modules.shapes.touch_zones import touch_zones

TOUCH_PCT = 1.4
SOURCE = {"zigzag": "zigzag", "pivots": "pivot", "atr": "ATR-zigzag"}
TREND_RULE = {"protected1": "protected low, 1 break", "protected2": "protected low, 2 breaks",
              "window": "last peaks and valleys"}


def _roles(levels: List[Dict], price: float) -> List[str]:
    above = sorted((l for l in levels if l["price"] > price and not l.get("on")), key=lambda l: l["price"])
    below = sorted((l for l in levels if l["price"] < price and not l.get("on")), key=lambda l: -l["price"])
    names = {}
    for side, word in ((above, "resistance above"), (below, "support below")):
        for n, l in enumerate(side):
            names[id(l)] = ("next " * n) + word
    return [("the level price is on" if l.get("on") else names[id(l)]) for l in levels]


def _level_how(l: Dict, f, c, yard: float, band_pct: float) -> str:
    n, src = len(l["points"]), SOURCE.get(c.swings, c.swings)
    made = (f"the {l['wall']} of the range price is in" if l.get("wall")
            else f"{n} {src} point{'s' if n != 1 else ''} grouped" if c.group == "channels"
            else f"one {src} point")
    band = (f"a {band_pct:.1f}% band ({yard:.1f}% move x {MOVE_BAND:g})" if c.band == "move"
            else f"a {band_pct:.1f}% band (5% of the 300-bar range)")
    return (f"{l['low']:,.0f}-{l['high']:,.0f}: {made}, within {band}. "
            f"Score {l['score']} = {parts_text(l['parts'])}. Kept by: {l.get('kept_by', '?')}.")


def _trend_how(t: Dict, f, c, end: int) -> str:
    a, b = int(t["points"][0]), int(t["points"][-1])
    pct = np.expm1(t["slope"]) * 100
    far = f" Out of the move's reach ({t['away_pct']:.1f}% away): drawn dotted." if t.get("far") else ""
    return (f"{t['direction'].capitalize()} ({TREND_RULE.get(c.trend, c.trend)}): "
            f"{pct:+.2f}%/day, from {f.day(a)} through {f.day(b)}.{far}")


def concept_story(df, end: int, f, levels: List[Dict], trends: List[Dict], c, yard: float,
                  band_pct: float) -> Dict:
    lines = []
    for l, role in zip(levels, _roles(levels, f.price_now)):
        lines.append({"role": role, "price": l["price"], "kind": "level", "points": l["points"],
                      "how": _level_how(l, f, c, yard, band_pct), "score": l["score"], "parts": l["parts"]})
    for t in trends:
        lines.append({"role": "the previous trend" if t.get("previous") else "the trend",
                      "price": at_bar(t, end), "kind": "trend", "points": t["points"],
                      "slope_pct_day": float(np.expm1(t["slope"]) * 100), "how": _trend_how(t, f, c, end)})
    for line in lines:
        dots = [int(b) for b in line["points"]]
        line["times"] = [f.time(b) for b in dots]
        line["dates"] = [f.day(b) for b in dots]
        line["zones"] = [{**z, "from_time": f.time(z["from_bar"]), "to_time": f.time(z["to_bar"]),
                          "from_date": f.day(z["from_bar"]), "to_date": f.day(z["to_bar"])}
                         for z in touch_zones(line["price"], TOUCH_PCT, f.high, f.low, end)
                         if any(z["from_bar"] <= b <= z["to_bar"] for b in dots)]
    return {"price_now": f.price_now, "current_move": f.now_move, "move_from": f.day(f.now_from_bar),
            "lines": lines}
