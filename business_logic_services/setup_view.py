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
import pandas as pd
from business_logic_services.precedents import picture_starts_at
from business_logic_services.setup_story import setup_story
from business_logic_services.swing_frame import swing_frame
from modules.shapes.swing_boxes import swing_boxes

MIN_POINTS_FOR_A_STORY = 3      # below this there is no structure to tell a story about


def picture_start(df: pd.DataFrame, end: int, size: float, band_pct: float, cache=None) -> float:
    """How far back the chart reaches: to the precedent of the level price is working now."""
    f = swing_frame(df, end, size, cache)
    if len(f) < MIN_POINTS_FOR_A_STORY:
        return 0.0
    return picture_starts_at(f.price_now, f.now_move, f.bars, f.prices, f.moves, band_pct, end)


def story_view(df: pd.DataFrame, end: int, size: float, levels: list, trend: Optional[Dict],
               band_pct: float, cache=None) -> Dict:
    """What each line on the chart is, and how it was found."""
    f = swing_frame(df, end, size, cache)
    if len(f) < MIN_POINTS_FOR_A_STORY or not levels:
        return {}
    # every dot's box, so a line can show the journeys of the dots it is made of
    boxes_by_bar = {b["bar"]: {**b, "from_time": f.time(b["from_bar"]), "to_time": f.time(b["to_bar"])}
                    for b in swing_boxes(f.tp, f.high, f.low, end)}
    story = setup_story(levels, trend, f.price_now, f.price_before, f.now_move, f.now_from_bar,
                        end, band_pct, f.day, f.bars, f.prices, f.moves, boxes_by_bar)
    for line in story["lines"]:
        line["times"] = [f.time(b) for b in line["points"]]
        line["dates"] = [f.day(b) for b in line["points"]]
    return story
