"""
Merge near-copy TREND lines (owner, 2026-09-24: "there are 3 trend lines again").
Levels are not merged here: they come out of one clustering of the dots
(business_logic_services/level_rule.py), so they never need a second pass.
"""
from typing import Dict, List
import numpy as np


def merge_trends(trends: List[Dict], now: float, price_pct: float, slope_pct: float = 0.08) -> List[Dict]:
    """Near-copies of the same trend become one line (owner: "there are 3 trend lines again").
    Two trends are the same when they run on the same side, sit within `price_pct` of each other
    at `now` and their slopes are within `slope_pct` (%/day). The strongest survives, with the
    longest reach of the group."""
    if not trends or price_pct <= 0:
        return trends
    gap = np.log(1 + price_pct / 100)
    at_now = lambda t: t["y1"] + t["slope"] * (now - t["x1"])
    groups: List[List[Dict]] = []
    for t in sorted(trends, key=lambda t: (-t["touches"], -(t["last"] - t["first"]))):
        same = next((g for g in groups if g[0]["role"] == t["role"]
                     and abs(at_now(g[0]) - at_now(t)) <= gap
                     and abs(np.expm1(g[0]["slope"]) - np.expm1(t["slope"])) * 100 <= slope_pct), None)
        if same is None:
            groups.append([t])          # the first of a group is its strongest: the list is sorted
        else:
            same.append(t)
    out = []
    for group in groups:
        best = group[0]
        out.append({**best, "first": min(t["first"] for t in group), "last": max(t["last"] for t in group),
                    "merged_from": len(group)})
    return out
