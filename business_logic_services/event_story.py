"""
Each event in words: what decided it, in prices, % and dates (owner, 2026-10-08: "i would like to
see the lines and how you made them, the events and how you decided them").
"""
from typing import Dict
import pandas as pd

NAMES = {"double_top": "Double top", "double_bottom": "Double bottom", "head_shoulders": "Head and shoulders",
         "inverse_head_shoulders": "Inverse head and shoulders", "cup_handle": "Cup and handle",
         "bull_flag": "Bull flag", "bear_flag": "Bear flag"}
CANDLE = {"pin": "a pin bar (hammer / shooting star)", "engulfing": "an engulfing candle",
          "piercing": "a piercing / dark cloud candle"}


def _n(x: float) -> str:
    return f"{x:,.0f}"


def _line(e: Dict) -> str:
    ln = e["line"]
    # by kind and price, not by role: the role is read on the event's own day, when a line just
    # broken is already on the other side of price ("breakout up through support below")
    what = "the trend line" if ln["kind"] == "trend" else "the level"
    lo, hi = e["line"].get("zone", [ln["value"], ln["value"]])
    return f"{what} {_n(ln['value'])} (zone {_n(lo)}-{_n(hi)})"


def _pattern(e: Dict, day) -> str:
    pts = ", ".join(f"{day(b)} {_n(p)}" for b, p in e["points"])
    neck = e["neckline"]
    edge = _n(neck["price"]) if neck["kind"] == "level" else "the sloped neckline"
    return (f"{NAMES[e['type']]}: {pts}. Closed {'under' if e['direction'] == 'down' else 'over'} {edge} "
            f"for the first time. Target {_n(e['target'])} (the pattern's height from the neckline).")


def why(e: Dict, index: pd.DatetimeIndex) -> str:
    day = lambda b: index[int(b)].strftime("%Y-%m-%d")
    t, way = e["type"], e["direction"]
    if e.get("pattern"):
        text = _pattern(e, day)
    elif t == "breakout":
        text = (f"Breakout {way} through {_line(e)}: {e['closes']} close(s) in a row "
                f"{'above' if way == 'up' else 'below'} the zone, {e['beyond_pct']:.1f}% past its edge; "
                f"price entered the zone on {day(e['from_bar'])} from the other side.")
    elif t == "fakeout":
        text = (f"Fakeout at {_line(e)}: closed beyond the zone on {day(e['from_bar'])}, went at most "
                f"{e['beyond_pct']:.1f}% past it, and closed back across the line {e['bars_out']} bar(s) "
                f"later. Points {way}.")
    elif t == "sweep":
        text = (f"Sweep at {_line(e)}: the wick went {e['beyond_pct']:.1f}% past the zone and the candle "
                f"closed back across the line. Points {way}.")
    elif t == "retest":
        text = (f"Retest of {_line(e)}: the first return to the zone, {e['bars_after']} bar(s) after the "
                f"breakout of {day(e['breakout_bar'])}, closed on the breakout side.")
    elif t == "bounce":
        text = (f"Bounce {way} at {_line(e)}: {e['bars_in']} bar(s) in the zone, then the first close out "
                f"of it on the side it came from.")
    elif t == "trend_change":
        text = f"Trend change: {e['was']} -> {way}; the new trend line is at {_n(e['line']['value'])}."
    else:
        text = t
    if e.get("confluence"):
        text += f" Confluence: {len(e['confluence'])} other line(s) in the zone."
    if e.get("candle"):
        text += f" Confirmed by {CANDLE[e['candle']]}."
    return text
