"""
The chart patterns over history: each day, the patterns completed that day from the peaks and valleys
KNOWN that day (a point counts from the bar that confirmed it - no lookahead), with "the same level"
taken from that day's band.
"""
from typing import Dict, Iterable, List
import pandas as pd
from modules.patterns.chart_patterns import cup_handle, double, head_shoulders
from modules.patterns.flag_patterns import flag, mirrored
from modules.shapes.sr_turning_points import PEAK
from modules.shapes.swing_sources import swing_points

PATTERN_TYPES = ("double_top", "double_bottom", "head_shoulders", "inverse_head_shoulders",
                 "cup_handle", "bull_flag", "bear_flag")
RECENT = 8                    # points a pattern can be made of: the longest (head and shoulders) has 5


def scan_patterns(df: pd.DataFrame, swings: str, size: float, band_by_day: Dict[int, float],
                  types: Iterable[str], cache: Dict) -> List[Dict]:
    types = set(types)
    if not types:
        return []
    tp = swing_points(df, swings, size, cache)
    high, low, close = (df[k].to_numpy() for k in ("High", "Low", "Close"))
    known = sorted(zip(tp["conf"], tp["idx"], tp["kind"]))
    flipped = mirrored(df) if "bear_flag" in types else None
    out, n = [], 0
    for d in sorted(band_by_day):
        while n < len(known) and known[n][0] <= d:
            n += 1
        pts = sorted((int(i), float(high[i] if k == PEAK else low[i]), int(k)) for _, i, k in known[max(0, n - RECENT):n])
        same = band_by_day[d]
        found = [
            "double_top" in types and double(pts, close, d, same, top=True),
            "double_bottom" in types and double(pts, close, d, same, top=False),
            "head_shoulders" in types and head_shoulders(pts, close, d, same, top=True),
            "inverse_head_shoulders" in types and head_shoulders(pts, close, d, same, top=False),
            "cup_handle" in types and cup_handle(pts, close, low, d, same),
            "bull_flag" in types and flag(df, d, True),
            "bear_flag" in types and flag(df, d, False, flipped),
        ]
        out += [{**p, "from_bar": p["points"][0][0], "pattern": True} for p in found if p]
    return out
