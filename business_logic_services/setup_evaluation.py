"""
Setups: the owner's drawn setups (ground truth) against the detector.
  resistance_flag_setups  owner setups holding a resistance line and a bull-flag box
  evaluate_setup          found = on the bar it was drawn at, the detector has a setup whose
                          resistance is within LINE_TOL of the drawn line there, and whose flag
                          span (pole start -> now) overlaps the drawn box by >= MIN_OVERLAP of
                          their union in time (Claude's tolerances)
  detection_episodes      every run of detections over the whole history, ready to draw
"""
from typing import Dict, List
import numpy as np
import pandas as pd
from modules.setups.resistance_flag import setup_at, scan, episodes
from modules.shapes.strong_resistance import line_value

LINE_TOL, MIN_OVERLAP = float(np.log(1.02)), 0.5


def resistance_flag_setups(store) -> List[Dict]:
    def has(s, kind, word):
        return any(d["kind"] == kind and word in d["label"].lower() for d in s["drawings"])
    return [s for s in store.setups_with_members()
            if s.get("author", "owner") == "owner" and has(s, "line", "resistance") and has(s, "box", "flag")]


def _bar(df: pd.DataFrame, t: int) -> int:
    seconds = (df.index - pd.Timestamp(0, tz="UTC")) // pd.Timedelta(seconds=1)
    return int(np.searchsorted(np.asarray(seconds), t))


def evaluate_setup(df: pd.DataFrame, setup: Dict) -> Dict:
    line = next(d for d in setup["drawings"] if d["kind"] == "line" and "resistance" in d["label"].lower())
    box = next(d for d in setup["drawings"] if d["kind"] == "box" and "flag" in d["label"].lower())
    now = _bar(df, max(d.get("drawn_at") or 0 for d in setup["drawings"]))
    res = {"name": setup["name"], "date": str(df.index[now].date()), "found": False, "line_gap": None, "flag_overlap": None}
    det = setup_at(df, now)
    res["detected"] = det
    if det is None:
        return {**res, "reason": "no setup detected on that day"}
    (x0, p0), (x1, p1) = [(_bar(df, p["time"]), np.log(p["price"])) for p in line["points"]]
    drawn = p0 + (p1 - p0) * (now - x0) / (x1 - x0)
    res["line_gap"] = float(line_value(det["resistance"], now) - drawn)
    b0, b1 = sorted(_bar(df, p["time"]) for p in box["points"])
    f0 = det["flag"]["pole_start"]
    inter = max(0, min(b1, now) - max(b0, f0) + 1)
    res["flag_overlap"] = inter / (max(b1, now) - min(b0, f0) + 1)
    res["found"] = abs(res["line_gap"]) <= LINE_TOL and res["flag_overlap"] >= MIN_OVERLAP
    return res


def _drawing(df, det, last):
    t = lambda i: int(df.index[i].timestamp())
    r, f = det["resistance"], det["flag"]
    x_end = min(last + 30, len(df) - 1)
    return ({"points": [{"time": t(r["x1"]), "price": float(np.exp(r["y1"]))},
                        {"time": t(x_end), "price": float(np.exp(line_value(r, x_end)))}]},
            {"points": [{"time": t(f["pole_start"]), "price": f["pole_low"]},
                        {"time": t(det["end"]), "price": max(f["pole_high"], f["flag_high"])}]})


def detection_episodes(df: pd.DataFrame) -> List[Dict]:
    out = []
    for ep in episodes(scan(df)):
        det = ep["setup"]
        line, box = _drawing(df, det, ep["last"])
        out.append({"first": ep["first"], "last": ep["last"], "days": ep["days"],
                    "first_date": str(df.index[ep["first"]].date()), "last_date": str(df.index[ep["last"]].date()),
                    "broken": det["broken"], "gap": det["gap"], "touches": det["resistance"]["touches"],
                    "rejection": det["resistance"]["rejection"], "flag": det["flag"], "line": line, "box": box})
    return out
