"""
The kept zigzag lines (zigzag_lines.py) in the shape the page draws and the setup card explains:
levels from their zigzag point to today, trend lines from their first point to today (to the break
when broken), and for each line what it is made of.
"""
from typing import Dict
import numpy as np
import pandas as pd
from business_logic_services.trend_structure import zigzag
from business_logic_services.frozen_zigzag import frozen_points
from business_logic_services.swing_frame import swing_frame
from business_logic_services.zigzag_lines import _at, at_day
from business_logic_services.zigzag_strength import words
from modules.shapes.sr_turning_points import PEAK
from modules.shapes.touch_zones import touch_zones

TOUCH_PCT = 1.5


def _day(df, b) -> str:
    return df.index[int(b)].strftime("%Y-%m-%d")


def _zones(df, price: float, bars, end: int):
    high, low, t = df["High"].to_numpy(), df["Low"].to_numpy(), df.index
    return [{**z, "from_time": int(t[z["from_bar"]].timestamp()), "to_time": int(t[z["to_bar"]].timestamp()),
             "from_date": _day(df, z["from_bar"]), "to_date": _day(df, z["to_bar"])}
            for z in touch_zones(price, TOUCH_PCT, high, low, end) if any(z["from_bar"] <= b <= z["to_bar"] for b in bars)]


def zigzag_page(df: pd.DataFrame, end: int, size: float, cache: Dict) -> Dict:
    g = at_day(df, end, size, cache)
    t = df.index
    levels, trends, story = [], [], []
    price = float(df["Close"].iloc[end])
    day = lambda bar: _day(df, bar)
    for l in g["levels"]:
        st = l["strength"]
        levels.append({"price": l["price"], "first": float(st["first"]), "last": float(end), "points": [float(b) for b in st["points"]],
                       "touches": st["touches"], "visits": st["touches"], "history": 0, "y": float(np.log(l["price"]))})
        story.append({"role": l["role"], "price": l["price"], "kind": "level", "points": st["points"], "strength": st,
                      "how": f"A line of {st['touches']} zigzag {l['made_by']} at {l['price']:,.0f}. "
                             + words(st, "level", day, price, l["price"])})
    for ln in g["trends"]:
        down, broken, st = ln["down"], ln["broken"], ln["strength"]
        name = ("down" if down else "up") + " trend line"
        role = f"broken {name}" if broken is not None else f"the {name}"
        trends.append({"x1": ln["x1"], "y1": ln["y1"], "slope": ln["slope"], "first": float(ln["points"][0]),
                       "last": float(broken if broken is not None else end), "far": False, "touches": st["touches"],
                       "direction": "down" if down else "up", "points": [float(b) for b in st["points"]]})
        a0, b0 = ln["points"]
        story.append({"role": role, "price": _at(ln, end), "kind": "trend", "points": st["points"], "strength": st,
                      "slope_pct_day": float(np.expm1(ln["slope"]) * 100),
                      "how": f"Drawn {_day(df, ln['born'])} through the {'peaks' if down else 'valleys'} {_day(df, a0)} "
                             f"{ln['prices'][0]:,.0f} and {_day(df, b0)} {ln['prices'][1]:,.0f}. "
                             + words(st, "trend", day, price, _at(ln, end), broken)})
    price_of = {p[0]: p[2] for p in g["points"]}
    for line in story:
        line["point_prices"] = [price_of.get(int(b), line["price"]) for b in line["points"]]   # each dot on its own point
        line["dates"] = [_day(df, b) for b in line["points"]]
        line["times"] = [int(t[int(b)].timestamp()) for b in line["points"]]
        line["zones"] = _zones(df, line["price"], [int(b) for b in line["points"]], end) if line["kind"] == "level" else []
    frozen = frozen_points(df, end, size, cache)
    f = swing_frame(df, end, size, cache)          # the move running now: the stars' window
    return {"levels": levels, "trends": trends, "zigzag": zigzag(df, end, size, cache, frozen),
            "story": {"price_now": float(df["Close"].iloc[end]), "current_move": f.now_move,
                      "move_from": _day(df, f.now_from_bar), "lines": story}}
