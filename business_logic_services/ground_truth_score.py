"""
Score what the code found against what the owner drew (2026-09-24: "did you compare to my ground
truth setup? remember the goal is to find setups like me?").

A drawn LINE is the unit. Horizontal drawings are matched against the zones, diagonals against the
trend lines, both at the price they hold "now". Found / missed / extra is the scoreboard the line
layer is driven by.
"""
from typing import Dict, List
import numpy as np

SCORED_KIND = "line"           # the only kind this scorer reads: boxes and sketches explain, never score
FLAT_PCT_PER_DAY = 0.02        # below this a drawn line counts as horizontal
SLOPE_TOL = 0.08               # %/day: how close a trend's slope must be to the drawn one


def _drawn_line(d: Dict) -> Dict:
    (t0, p0), (t1, p1) = [(p["time"], p["price"]) for p in d["points"]]
    days = max((t1 - t0) / 86400, 1e-9)
    slope_pct_day = (np.log(p1) - np.log(p0)) / days * 100
    return {"label": d["label"], "price_at_end": float(p1), "slope_pct_day": float(slope_pct_day),
            "horizontal": bool(abs(slope_pct_day) <= FLAT_PCT_PER_DAY)}


def score_against_drawings(drawings: List[Dict], found: Dict, price_now: float, tol_pct: float = 3.0) -> Dict:
    tol = np.log(1 + tol_pct / 100)
    zones, trends = list(found.get("zones", [])), list(found.get("trends", []))
    used_zone, used_trend, lines = set(), set(), []
    for d in drawings:
        if d.get("kind") != SCORED_KIND:
            continue
        drawn = _drawn_line(d)
        match, kind = None, None
        if drawn["horizontal"]:
            near = [(i, z) for i, z in enumerate(zones) if abs(np.log(z["price"] / drawn["price_at_end"])) <= tol]
            if near:
                i, z = min(near, key=lambda iz: abs(np.log(iz[1]["price"] / drawn["price_at_end"])))
                match, kind = z["price"], "zone"
                used_zone.add(i)
        else:
            near = [(i, t) for i, t in enumerate(trends)
                    if abs(np.log(t["at_now"] / drawn["price_at_end"])) <= tol
                    and abs(t["slope_pct_day"] - drawn["slope_pct_day"]) <= SLOPE_TOL]
            if near:
                i, t = min(near, key=lambda it: abs(it[1]["slope_pct_day"] - drawn["slope_pct_day"]))
                match, kind = t["at_now"], "trend"
                used_trend.add(i)
        lines.append({"label": drawn["label"], "drawn": drawn["price_at_end"], "found": match is not None,
                      "by": None if match is None else float(match), "kind": kind,
                      "horizontal": drawn["horizontal"]})
    extra = ([{"price": float(z["price"]), "kind": "zone"} for i, z in enumerate(zones) if i not in used_zone]
             + [{"price": float(t["at_now"]), "kind": "trend"} for i, t in enumerate(trends) if i not in used_trend])
    return {"total": len(lines), "found": int(sum(l["found"] for l in lines)),
            "missed": int(sum(not l["found"] for l in lines)), "lines": lines, "extra": extra,
            "price_now": float(price_now)}
