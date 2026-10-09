"""
The trend-continuation entry and the trend exit (2026-10-09). His backtest made +1.7% a trade on a
market that went 6k -> 100k+: "does not make sense when the price made hundreds if not thousands of
percents moves". Two causes, measured:
  - at an all-time high there is no resistance line above to break (a line needs two zigzag points),
    so the breakout entry was out of the market for all of 2020-10 -> 2021-04 (+493%) - his own note,
    2025-10-03: "there is no next resistance because its all time high"
  - selling at the next line capped every trade at a few %

  entry   in an up trend - an unbroken up trend line under price (the trend line's slope IS the
          direction, 2026-10-09) - the day the zigzag confirms a new higher low: buy, stop at that low
          (Dow: the up trend holds while its higher lows hold)
  exit    for every trade: no target; the stop rises to each new zigzag valley under price (the trend's
          last higher low) and never falls; out when a low reaches it
"""
from typing import Dict, List
from modules.shapes.sr_turning_points import PEAK


def higher_low_entries(days, points_at, trend_at) -> List[Dict]:
    """`trend_at(day)`: the direction that day from the trend lines (zigzag_lines.direction_at)."""
    out, seen = [], set()
    for d in days:
        pts = points_at(d)
        if not pts or pts[-1][3] != d or pts[-1][1] == PEAK:
            continue                                   # no valley confirmed today
        vs = [p for p in pts if p[1] != PEAK]
        if len(vs) < 2 or vs[-1][2] <= vs[-2][2] or vs[-1][0] in seen:
            continue                                   # not a higher low
        if trend_at(d) != "up":
            continue
        seen.add(vs[-1][0])
        out.append({"bar": d, "kind": "higher low", "stop": vs[-1][2], "target": float("inf"),
                    "low": {"bar": vs[-1][0], "price": vs[-1][2]}, "prev_low": {"bar": vs[-2][0], "price": vs[-2][2]}})
    return out


def last_higher_low(points_at):
    """The trailing stop: the zigzag's last confirmed valley under price that day."""
    def stop_at(day: int, price: float):
        vs = [p[2] for p in points_at(day) if p[1] != PEAK and p[2] < price]
        return vs[-1] if vs else None
    return stop_at
