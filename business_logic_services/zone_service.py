"""
The zone view: price zones at a swing size, and the ladder read from the current price
(owner, 2026-09-24: "what is my current support and resistance ... and whats the next ones").
Only candles up to `end` are used.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from modules.shapes.price_zones import ladder, price_zones
from modules.shapes.sr_turning_points import turning_points, PEAK

LOOK_BACK_FOR_DIRECTION = 10        # bars used to tell where price came from


def zone_view(df: pd.DataFrame, end: int, size: float, band_pct: Optional[float] = None,
              min_visits: int = 2, n_each: int = 3, cache: Optional[Dict] = None) -> Dict:
    cache = cache if cache is not None else {}
    tp = cache[size] if size in cache else cache.setdefault(size, turning_points(df, size))
    known = tp["conf"] <= end
    x, y, kind = tp["idx"][known].astype(float), tp["y"][known], tp["kind"][known]
    price_now = float(df["Close"].iloc[end])
    price_before = float(df["Close"].iloc[max(0, end - LOOK_BACK_FOR_DIRECTION)])
    band = band_pct if band_pct is not None else size * 100 / 2
    zones = price_zones(x, y, kind, band, price_now, end)
    lad = ladder(zones, price_now, price_before, n_each, min_visits)
    shown = [z for z in [lad["on"], *lad["above"], *lad["below"]] if z]
    for z in shown:
        z["first_time"] = int(df.index[int(z["first_visit"])].timestamp())
        z["last_time"] = int(df.index[int(z["last_visit"])].timestamp())
        z["now_time"] = int(df.index[end].timestamp())          # the band runs on to "now"
        z["visit_times"] = [int(df.index[int(p)].timestamp()) for p in z["points"]]
    return {"end": int(end), "size": size, "band_pct": band, "price_now": price_now,
            "price_before": price_before, "zones": shown, "on": lad["on"],
            "above": lad["above"], "below": lad["below"], "candidates": len(zones)}
