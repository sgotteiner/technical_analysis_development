"""
Export the S/R lines tool (modules/shapes/sr_lines.py) to a standalone replay page:
ui/sr_viewer.html — step a "now" marker through BTC daily history and see the 4 lines
(higher/lower x support/resistance) computed from data up to "now" only.

Usage:  python scripts/export_sr_lines.py
"""
import os
import sys
import json
import pandas as pd

sys.path.append(os.path.abspath("."))
import numpy as np
from modules.shapes.sr_lines import TOUCH_TOL
from modules.shapes.sr_pipes import sr_lines_at, swing_legs, pipe_width, LEVELS
from helpers.export_helpers import read_ui_file

UI_DIR = "ui"
OUTPUT = os.path.join(UI_DIR, "sr_viewer.html")
FIRST_SNAPSHOT = max(cfg["period"] for cfg in LEVELS.values())
KEYS = ["higher_support", "higher_resistance", "lower_support", "lower_resistance"]


def build_payload(daily: pd.DataFrame):
    candles = [{"time": int(t.timestamp()), "open": round(o, 1), "high": round(h, 1), "low": round(l, 1),
                "close": round(c, 1)}
               for t, o, h, l, c in zip(daily.index, daily["Open"], daily["High"], daily["Low"], daily["Close"])]
    snapshots, cache = {}, {}                 # turning points computed once, filtered per day
    for end in range(FIRST_SNAPSHOT, len(daily)):
        lines = sr_lines_at(daily, end, cache=cache)
        pipes = {}
        for lvl, cfg in LEVELS.items():
            sup, res = lines[f"{lvl}_support"], lines[f"{lvl}_resistance"]
            legs = swing_legs(daily, end, cfg["period"], cfg["magnitude"], cache.get(cfg["magnitude"]))
            pipes[lvl] = [None if sup is None else round(pipe_width(sup, res), 5),
                          round(float(legs.max()), 5) if len(legs) else None]
        snapshots[end] = {"lines": [None if lines[k] is None else
                                    [lines[k]["x1"], round(lines[k]["y1"], 6), round(lines[k]["slope"], 8), lines[k]["touches"],
                                     lines[k]["last_touch"]]
                                    for k in KEYS], "pipes": pipes}
    settings = {"levels": LEVELS, "touch_pct": round(float(np.expm1(TOUCH_TOL)) * 100, 2), "keys": KEYS}
    return candles, snapshots, settings


def export():
    daily = pd.read_csv(os.path.join("data", "btc_1d_extended.csv"), index_col=0)
    daily.index = pd.to_datetime(daily.index, utc=True)
    candles, snapshots, settings = build_payload(daily)
    html = read_ui_file(UI_DIR, "sr_lines.html")
    html = html.replace("/* LIGHTWEIGHT_CHARTS_JS_PLACEHOLDER */", read_ui_file(UI_DIR, "lightweight-charts.js"))
    html = html.replace("/* DATA_CANDLES */", json.dumps(candles))
    html = html.replace("/* DATA_SNAPSHOTS */", json.dumps(snapshots))
    html = html.replace("/* DATA_SETTINGS */", json.dumps(settings))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"S/R viewer exported: {OUTPUT}  ({len(candles)} candles, {len(snapshots)} daily snapshots)")


if __name__ == "__main__":
    export()
