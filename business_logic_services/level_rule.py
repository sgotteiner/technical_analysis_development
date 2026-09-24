"""
The level rule, one mechanism (owner, 2026-09-24: "i hope you didnt do a band aid and actually
solved it generally").

  1. cluster the DOTS into price bands of `merge_pct` (modules/shapes/price_zones.py): each band
     is bounded, so nothing chains across the chart, and its line sits at the strongest price;
  2. a cluster is SHOWN when price has been at it recently (his "find the recent S/R first"),
     or when it is one of the nearest clusters above / below price with nothing recent - a TARGET
     (his "next resistance" 106k);
  3. the strength of a cluster is its visits, and visits before the recent window are its history.

Nothing is merged after the fact: there is one clustering, and the lines come out of it.
"""
from typing import Dict, List
import numpy as np
from modules.shapes.price_zones import ladder, price_zones

TARGET_MIN_VISITS = 2


def _as_level(z: Dict, start: float, from_history: bool = False) -> Dict:
    points = z["points"]
    return {"price": z["price"], "y": z["y"], "low": z["low"], "high": z["high"],
            "touches": z["touches"], "visits": z["visits"],
            "history": int(sum(1 for p in points if p < start)),
            "first": z["first_visit"], "last": z["last_visit"], "anchor": z["last_visit"],
            "points": points, "at_price_now": z["at_price_now"], "from_history": from_history,
            "merged_from": z["touches"]}


def levels_from_points(x: np.ndarray, y: np.ndarray, kinds: np.ndarray, start: float, band_pct: float,
                       price_now: float, price_before: float, end: float, min_visits: int = 2,
                       targets_each_way: int = 2, target_dots=None, target_band_pct: float = 0.0,
                       top: int = 0, prefer: str = "recent") -> List[Dict]:
    """Clusters of dots, shown when they are being touched now or are the next ones up and down.
    The targets use their own, bigger dots: the ladder ("next resistance" 106k) is a bigger-scale
    structure than the lines price is working with right now."""
    if not len(x):
        return []
    zones = price_zones(x, y, kinds, band_pct, price_now, end)
    recent = [_as_level(z, start) for z in zones
              if z["last_visit"] >= start and z["visits"] >= min_visits]
    # which cluster wins a crowded area: measured against the owner's own lines, the most
    # recently visited one matches his eye better than the one with the most visits
    rank = (lambda lv: (not lv["at_price_now"], -lv["last"], -lv["visits"])) if prefer == "recent"         else (lambda lv: (not lv["at_price_now"], -lv["visits"], -lv["last"]))
    recent.sort(key=rank)
    if top:
        recent = recent[:top]          # `top` limits the recent lines; targets never lose a slot
    shown = {round(lv["price"], 2): lv for lv in recent}
    if targets_each_way:
        big = zones
        if target_dots is not None and len(target_dots[0]):
            bx, by, bk = target_dots
            big = price_zones(bx, by, bk, target_band_pct or band_pct * 2, price_now, end)
        # targets are rarer than the lines price is working with: two visits is enough,
        # otherwise the 106k next resistance (2 visits) never shows
        lad = ladder(big, price_now, price_before, targets_each_way, TARGET_MIN_VISITS)
        for z in [lad["on"], *lad["above"], *lad["below"]]:
            if z is not None and round(z["price"], 2) not in shown:
                shown[round(z["price"], 2)] = _as_level(z, start, from_history=True)
    # one last pass over EVERYTHING on the list: recent lines and targets come from two different
    # clusterings, so two of them can still land a hair apart. The strongest keeps the place.
    gap = np.log(1 + band_pct / 100)
    out: List[Dict] = []
    for lv in sorted(shown.values(), key=lambda l: (not l["at_price_now"], l["from_history"],
                                                    *((-l["last"], -l["visits"]) if prefer == "recent"
                                                      else (-l["visits"], -l["last"])))):
        if not any(abs(np.log(lv["price"] / kept["price"])) < gap for kept in out):
            out.append(lv)
    return out
