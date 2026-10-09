"""
His setup's lines on every day - what the S/R algorithm drew that day, with the page's own settings
(screen_lines). The strategies read THESE lines, so a breakout in a backtest is the breakout of a line
he would have seen on that date (owner, 2026-10-08: "i dont care about some shit dots i care about my
setup"). Computed once per setting (~9 minutes) and kept on disk.
"""
import hashlib
import json
import os
import pickle
from typing import Dict
import pandas as pd
from business_logic_services.screen_lines import screen_lines
from business_logic_services.swing_view import swing_points
from schemas.sr_view_schema import LinesConfig

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache", "setup_history")
FIRST_DAY = "2018-06-01"
VERSION = 6              # bump when the line rules change: the cache on disk is per rules, not only per setting
# what the page sends for "recent levels + their history" (ui/js/sr_playground/points_controller.js)
PAGE = LinesConfig(mode="owner", tol_pct=1.5, min_touches=3, top=6, anchor_days=120, max_history=2,
                   merge_pct=0, targets_each_way=2, min_visits=2, prefer="recent")


def _slim(g: Dict) -> Dict:
    st = g.get("story") or {}
    return {"move_from": st.get("move_from"),
            "lines": [{"role": l["role"], "kind": l.get("kind", "level"), "price": float(l["price"]),
                       "slope_pct_day": l.get("slope_pct_day"), "strength": l.get("strength")}
                      for l in st.get("lines", [])]}


def setup_history(df: pd.DataFrame, cfg: LinesConfig = PAGE, size: float = 0.07, cache: Dict = None) -> Dict[int, Dict]:
    cache = cache if cache is not None else {}
    stamp = f"v{VERSION}|{len(df)}|{df.index[-1]}|{float(df['Close'].iloc[-1])}|{size}|{cfg.model_dump_json()}"
    path = os.path.join(CACHE_DIR, hashlib.sha1(stamp.encode()).hexdigest()[:16] + ".pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return pickle.load(f)
    first = int(df.index.searchsorted(pd.Timestamp(FIRST_DAY, tz="UTC")))
    out = {}
    for d in range(first, len(df)):
        try:
            out[d] = _slim(screen_lines(df, d, size, cfg, swing_points(df, d, size, cache), cache))
        except ValueError:
            out[d] = {"move_from": None, "lines": []}
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(out, f)
    return out


if __name__ == "__main__":
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from scripts.sr_playground import load_daily
    h = setup_history(load_daily())
    print(len(h), "days")
