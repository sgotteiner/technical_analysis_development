"""
The setup in words, and how far back the picture reaches.

Both answers come from the same backward search (business_logic_services/precedents.py): walk back
for the previous time price was at this level and stop at the first move of a comparable size -
"30 here 30 then ... you found something similar like i did and described you stop. you dont check
the entire history" (owner, 2026-10-03).

The story explains the lines the chart is ALREADY drawing and never finds its own: the two showing
"completely different numbers" was the worst defect of the session that built this.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from business_logic_services.precedents import picture_starts_at
from business_logic_services.setup_story import setup_story
from business_logic_services.swing_frame import swing_frame
from modules.shapes.swing_boxes import swing_boxes
from modules.shapes.touch_zones import touch_zones

MIN_POINTS_FOR_A_STORY = 3      # below this there is no structure to tell a story about


def picture_start(df: pd.DataFrame, end: int, size: float, band_pct: float, cache=None) -> float:
    """How far back the chart reaches: to the precedent of the level price is working now."""
    f = swing_frame(df, end, size, cache)
    if len(f) < MIN_POINTS_FOR_A_STORY:
        return 0.0
    return picture_starts_at(f.price_now, f.now_move, f.bars, f.prices, f.moves, band_pct, end)


def _trend_size(trend: Dict, high, low, end: int) -> Dict:
    """How far the trend has carried price: from where it began to its furthest point - for a
    previous trend, up to where the range took over. "would be nice to know the trend size"
    (owner, 2026-10-07)."""
    a, up = int(trend["first"]), trend["direction"] == "up"
    stop = end
    if trend.get("previous"):
        stop = int(max(trend.get("peaks", []) + trend.get("valleys", []) or [end]))
    seg = high[a:stop + 1] if up else low[a:stop + 1]
    j = a + int(np.argmax(seg) if up else np.argmin(seg))
    start, far = float(low[a] if up else high[a]), float(seg.max() if up else seg.min())
    return {"size_pct": (far / start - 1) * 100, "size_from": [a, start], "size_to": [j, far]}


def story_view(df: pd.DataFrame, end: int, size: float, levels: list, trend: Optional[Dict],
               band_pct: float, cache=None, touch_pct: float = 1.4) -> Dict:
    """What each line on the chart is, how it was found, and the zones where price worked it.

    `touch_pct` is the TOUCH tolerance, not the clustering band: his own drawn boxes are 2.85% and
    2.72% tall, which is +-1.4%, and the band that groups dots into a level (half the swing size,
    3.5% at 7%) makes zones more than twice that tall.
    """
    f = swing_frame(df, end, size, cache)
    if len(f) < MIN_POINTS_FOR_A_STORY or not levels:
        return {}
    # every dot's box, so a line can show the journeys of the dots it is made of
    boxes_by_bar = {b["bar"]: {**b, "from_time": f.time(b["from_bar"]), "to_time": f.time(b["to_bar"])}
                    for b in swing_boxes(f.tp, f.high, f.low, end)}
    if trend and trend.get("direction") in ("up", "down"):
        trend = {**trend, **_trend_size(trend, f.high, f.low, end)}
    story = setup_story(levels, trend, f.price_now, f.now_direction > 0, f.now_move, f.now_from_bar,
                        end, band_pct, f.day, f.bars, f.prices, f.moves, boxes_by_bar)
    for line in story["lines"]:
        line["times"] = [f.time(b) for b in line["points"]]
        line["dates"] = [f.day(b) for b in line["points"]]
        # the boxes that belong to THIS line: where price worked it, as zones rather than dots
        # (owner, 2026-10-05: "not touch dots like you do. touch zones")
        # only where price TURNED at the line - a zone holding one of the line's own zigzag points,
        # not every stretch where price crossed it (2026-10-07: "its not on points of the zigzag")
        dots = [int(b) for b in line.get("points") or []]
        line["zones"] = [{**z, "from_time": f.time(z["from_bar"]), "to_time": f.time(z["to_bar"]),
                          "from_date": f.day(z["from_bar"]), "to_date": f.day(z["to_bar"])}
                         for z in touch_zones(line.get("price") or 0.0, touch_pct, f.high, f.low, end)
                         if any(z["from_bar"] <= b <= z["to_bar"] for b in dots)]
    return story
