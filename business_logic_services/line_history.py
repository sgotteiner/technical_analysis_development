"""
The lines as they were on each day - what the events are judged against (owner, 2026-10-08: "the
events and how you decided them").

An event on day d may only use the lines known on day d: a breakout of a line drawn later is
lookahead. So the concept lines are computed for EVERY day once, kept on disk per setting, and each
day keeps only what an event needs: each line's zone and, for a trend, its equation.
"""
import hashlib
import json
import os
import pickle
from dataclasses import asdict
from typing import Dict, List
import numpy as np
import pandas as pd
from business_logic_services.line_concepts import Concepts, concept_lines

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache", "line_history")
FIRST_DAY = "2018-06-01"          # the start of every measurement so far


def _slim(day: int, g: Dict) -> Dict:
    levels = [{"id": f"L{l['price']:.0f}", "kind": "level", "price": float(l["price"]),
               "low": float(l["low"]), "high": float(l["high"]), "role": role}
              for l, role in zip(g["levels"], _roles(g))]
    trends = [{"id": f"T{t['x1']:.0f}{t['direction'][0]}", "kind": "trend", "direction": t["direction"],
               "x1": float(t["x1"]), "y1": float(t["y1"]), "slope": float(t["slope"]),
               "previous": bool(t.get("previous")), "far": bool(t.get("far"))} for t in g["trends"]]
    return {"bar": day, "levels": levels, "trends": trends, "band_pct": float(g["band_pct"]),
            "move_pct": float(g["move_pct"])}


def _roles(g: Dict) -> List[str]:
    by_price = {round(l["price"]): l["role"] for l in g["story"].get("lines", []) if l["kind"] == "level"}
    return [by_price.get(round(l["price"]), "level") for l in g["levels"]]


def _key(df: pd.DataFrame, c: Concepts, size: float) -> str:
    stamp = f"{len(df)}|{df.index[-1]}|{float(df['Close'].iloc[-1])}|{size}|{json.dumps(asdict(c), sort_keys=True)}"
    return hashlib.sha1(stamp.encode()).hexdigest()[:16]


def line_history(df: pd.DataFrame, c: Concepts, size: float, cache: Dict) -> Dict[int, Dict]:
    """{day: that day's lines} from FIRST_DAY to the last bar. Computed once per setting."""
    key = ("line_history", _key(df, c, size))
    if key in cache:
        return cache[key]
    path = os.path.join(CACHE_DIR, key[1] + ".pkl")
    if os.path.exists(path):
        with open(path, "rb") as f:
            cache[key] = pickle.load(f)
        return cache[key]
    first = int(df.index.searchsorted(pd.Timestamp(FIRST_DAY, tz="UTC")))
    out = {d: _slim(d, concept_lines(df, d, c, size, cache)) for d in range(first, len(df))}
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(out, f)
    cache[key] = out
    return out


def value_at(line: Dict, bar: float) -> float:
    """A line's price at a bar: a level is flat, a trend line runs on its slope (log price)."""
    if line["kind"] == "level":
        return line["price"]
    return float(np.exp(line["y1"] + line["slope"] * (bar - line["x1"])))
