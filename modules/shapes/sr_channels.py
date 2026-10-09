"""
"Support Resistance Channels" by LonesomeTheBlue - the most used open-source S/R script on
TradingView (47.5K uses), ported with its default settings so the owner can compare it with his
own lines (owner, 2026-10-08: "in trading view i saw some sr indicators with over 30k and 40k stars").

  1. Pivots: a high that is the highest of `period` bars on each side (a low: the lowest).
  2. For each pivot, a channel: every other pivot that fits while the channel stays no wider than
     `width_pct` of the high-low range of the last 300 bars.
  3. Strength = 20 per pivot in the channel + one per bar of the last `loopback` whose high or low
     is inside it.
  4. Strongest first; a channel overlapping a stronger one is dropped; at most `max_n` kept.
  5. Ours, not the script's: of those, the nearest EACH_SIDE above and below price are shown - his
     "at most 4 lines". Measured 2026-10-08 at his 10 reviewed dates: the script's 6 find 13 of his
     20 lines with 60 drawn; the nearest 2 each side find the same 13 with 31 drawn.

Its numbers are the script's defaults, not ours: they are fixed bar counts and a fixed %, which our
own rules avoid - kept as they are so this is the script he saw, not our version of it.
"""
from typing import Dict, List
import numpy as np

PERIOD, WIDTH_PCT, LOOKBACK, RANGE_BARS, MAX_N, PER_PIVOT = 10, 5.0, 290, 300, 6, 20
EACH_SIDE = 2


def _pivots(high: np.ndarray, low: np.ndarray, end: int, period: int, lookback: int) -> List[tuple]:
    """(bar, price) of the pivots known at `end`: a pivot needs `period` bars after it."""
    out = []
    for i in range(max(period, end - lookback), end - period + 1):
        win = slice(i - period, i + period + 1)
        if high[i] == high[win].max():
            out.append((i, float(high[i])))
        if low[i] == low[win].min():
            out.append((i, float(low[i])))
    return out


def range_width(high: np.ndarray, low: np.ndarray, end: int, width_pct: float = WIDTH_PCT) -> float:
    """The widest a channel may be: a share of the high-low range of the last RANGE_BARS bars."""
    rng = slice(max(0, end - RANGE_BARS + 1), end + 1)
    return float((high[rng].max() - low[rng].min()) * width_pct / 100)


def group_channels(points: List[tuple], width: float) -> List[Dict]:
    """For each (bar, price) point, the channel of every point that fits while it stays no wider
    than `width` - the script's own grouping, one channel per point (they overlap; pick with
    `non_overlapping`)."""
    out = []
    for _, p in points:
        lo = hi = p
        members = []
        for b, q in points:
            if (hi - q if q <= hi else q - lo) <= width:
                lo, hi = min(lo, q), max(hi, q)
                members.append((b, q))
        out.append({"lo": lo, "hi": hi, "members": members})
    return out


def bars_inside(c: Dict, high: np.ndarray, low: np.ndarray) -> int:
    """Bars whose high or low is inside the channel."""
    return int((((high >= c["lo"]) & (high <= c["hi"])) | ((low >= c["lo"]) & (low <= c["hi"]))).sum())


def non_overlapping(channels: List[Dict], key, max_n: int) -> List[Dict]:
    """Best first by `key`; a channel overlapping a better one is dropped."""
    chosen: List[Dict] = []
    for c in sorted(channels, key=lambda c: -key(c)):
        if any(c["lo"] <= o["hi"] and c["hi"] >= o["lo"] for o in chosen):
            continue
        chosen.append(c)
        if len(chosen) == max_n:
            break
    return chosen


def sr_channels(high: np.ndarray, low: np.ndarray, close: np.ndarray, end: int,
                period: int = PERIOD, width_pct: float = WIDTH_PCT, lookback: int = LOOKBACK,
                max_n: int = MAX_N) -> List[Dict]:
    """The channels at `end`, strongest first, as levels the page draws."""
    pivots = _pivots(high, low, end, period, lookback)
    if not pivots:
        return []
    width = range_width(high, low, end, width_pct)
    channels = group_channels(pivots, width)
    recent = slice(max(0, end - lookback), end + 1)
    for c in channels:
        c["strength"] = PER_PIVOT * len(c["members"]) + bars_inside(c, high[recent], low[recent])
    chosen = non_overlapping(channels, lambda c: c["strength"], max_n)
    now = float(close[end])
    mid = lambda c: (c["lo"] + c["hi"]) / 2
    below = sorted([c for c in chosen if mid(c) < now], key=mid, reverse=True)[:EACH_SIDE]
    above = sorted([c for c in chosen if mid(c) >= now], key=mid)[:EACH_SIDE]
    return [_as_level(c, now, end) for c in below + above]


def _as_level(c: Dict, now: float, end: int) -> Dict:
    mid = (c["lo"] + c["hi"]) / 2
    on = c["lo"] <= now <= c["hi"]
    members = sorted({b for b, _ in c["members"]})
    return {"price": mid, "high": c["hi"], "low": c["lo"], "y": float(np.log(mid)),
            "points": [float(b) for b in members], "touches": len(members), "visits": len(members), "history": 0,
            "first": float(members[0]), "last": float(end), "strength_score": c["strength"],
            "role": "on" if on else ("support" if mid < now else "resistance"),
            "at_price_now": on, "on": on, "source": "S/R Channels (LonesomeTheBlue)"}
