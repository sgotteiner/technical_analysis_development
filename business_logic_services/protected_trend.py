"""
The trend's direction as the literature keeps it: a running state, not a window of the last steps
(Dow Theory; the "market structure" indicators, BOS / CHoCH - tried at the owner's request,
2026-10-08: "maybe there are zigzag pine indicators that already work or rules that i dont need to
discover myself").

  up    a close over the last peak is a higher high; the valley before it becomes the PROTECTED
        low. The trend stays up until a close goes under that low.
  down  the mirror: a close under the last valley protects the peak before it.

A small bounce never moves the protected low, so it cannot end a trend - which is what broke the
counted rule twice ("2 higher highs and 2 higher lows" read off a window). A break is judged on the
CLOSE, so a wick through it is not a break (Murphy). How many breaks it takes is BREAKS.

Read at the trend's own size (the move's scale), never at a fixed one: at 7% it lost 4 of his 7
up / down readings, at the move's scale it matched all 7.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from business_logic_services.swing_frame import turning_points_cached
from modules.shapes.sr_turning_points import PEAK

UP, DOWN = "up", "down"
# How many breaks change the trend. 1 is the literature (a CHoCH). 2 is his rule - "there is no trend
# change if not at least 2 such" (2026-10-07) - and is kept as the switch: measured 2026-10-08, 1 loses
# his 29,000 resistance at 2022-07-22 (the trend turns up from the June low), 2 loses his down trend
# at 2026-02-13 (at the move's scale the 2023-2025 up trend has been broken only once).
BREAKS = 1


def _run(df: pd.DataFrame, tp: Dict, breaks: int = BREAKS) -> Dict[str, np.ndarray]:
    """Day by day: the direction, and the bar where that trend began (its starting extreme)."""
    close, high, low = df["Close"].to_numpy(), df["High"].to_numpy(), df["Low"].to_numpy()
    confirmed_on: Dict[int, list] = {}
    for i, k, c in zip(tp["idx"], tp["kind"], tp["conf"]):
        confirmed_on.setdefault(int(c), []).append((int(i), int(k)))
    n = len(df)
    direction, began = np.full(n, None, dtype=object), np.full(n, -1, dtype=int)
    peaks, valleys = [], []                         # confirmed (bar, price), oldest first
    state, protected, flipped = None, None, 0
    pending = None                  # after one break: (its bar, the close that undoes it)
    for d in range(n):
        for i, k in confirmed_on.get(d, []):
            (peaks if k == PEAK else valleys).append((i, high[i] if k == PEAK else low[i]))
        if state is None:
            if len(peaks) < 2 or len(valleys) < 2:
                continue
            state = UP if peaks[-1][1] > peaks[-2][1] else DOWN
            protected = valleys[-1][1] if state == UP else peaks[-1][1]
        sign = 1 if state == UP else -1             # +1: up is "with the trend"
        last_with = peaks[-1][1] if state == UP else valleys[-1][1]
        last_against = valleys[-1][1] if state == UP else peaks[-1][1]
        flip = False
        if pending is not None:
            since, undo = pending
            # the second step: a turn against the trend confirmed AFTER the first break (a bounce
            # that made a lower high), then a close past it - a second lower low
            turns = [p for b, p in (valleys if state == UP else peaks) if b >= since]
            if sign * (close[d] - undo) > 0:        # back past the trend's own extreme: noise
                pending = None
            elif turns and sign * (close[d] - turns[-1]) < 0:   # "at least 2 such"
                flip = True
        elif sign * (close[d] - last_with) > 0:     # a new extreme with the trend: protect the
            protected = last_against                # turn before it
        elif sign * (close[d] - protected) < 0:     # one break of the protected low, on a close
            pending = (d, last_with)                # a close back over the last peak undoes it
            flip = breaks == 1
        if flip:
            ext = np.argmax(high[flipped:d + 1]) if state == UP else np.argmin(low[flipped:d + 1])
            flipped += int(ext)                     # the new trend began at the old one's extreme
            state, pending = (DOWN if state == UP else UP), None
            protected = peaks[-1][1] if state == DOWN else valleys[-1][1]
        direction[d], began[d] = state, flipped
    return {"direction": direction, "began": began}


def protected_trend(df: pd.DataFrame, end: int, size: float,
                    cache: Optional[Dict] = None, breaks: int = BREAKS) -> Optional[Dict]:
    """The direction at `end` and the bar its trend began at. No lookahead: every decision on day d
    uses only points confirmed by d and closes up to d."""
    key = ("protected", size, breaks)
    if cache is None or key not in cache:
        run = _run(df, turning_points_cached(df, size, cache), breaks)
        if cache is None:
            return _at(run, end)
        cache[key] = run
    return _at(cache[key], end)


def _at(run: Dict, end: int) -> Optional[Dict]:
    if run["direction"][end] is None:
        return None
    return {"direction": run["direction"][end], "began": int(run["began"][end])}
