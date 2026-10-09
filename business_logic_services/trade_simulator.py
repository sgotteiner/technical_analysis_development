"""
Trades from signals on daily candles: in at the signal day's close, out at the stop, the target, or
after MAX_HOLD bars. Each trade knows its R (the result over the risk taken) so strategies with
different stops compare.

  same candle reaches both stop and target -> counted as the stop (a daily candle does not say which
  came first; assuming the worst keeps the result honest)
  FEE_PCT each way
  one trade at a time unless `overlap` (the comparison of every day uses overlap: it is an average,
  not an account)
"""
from typing import Dict, List
import numpy as np

FEE_PCT = 0.1             # each way - a stated guess for a spot exchange
MAX_HOLD = 120            # bars - a stated guess: a trade that reached neither line is closed


def simulate(close, high, low, sigs: List[Dict], overlap: bool = False) -> List[Dict]:
    trades, free_from = [], -1
    fee = FEE_PCT / 100
    for s in sorted(sigs, key=lambda s: s["bar"]):
        d = s["bar"]
        if (not overlap and d <= free_from) or d + 1 >= len(close):
            continue
        entry, stop, target = close[d], s["stop"], s["target"]
        if not stop < entry < target:
            continue
        exit_bar, exit_price, how = min(d + MAX_HOLD, len(close) - 1), None, "time"
        for k in range(d + 1, min(d + MAX_HOLD, len(close) - 1) + 1):
            if low[k] <= stop:
                exit_bar, exit_price, how = k, stop, "stop"; break
            if high[k] >= target:
                exit_bar, exit_price, how = k, target, "target"; break
        if exit_price is None:
            exit_price = close[exit_bar]
        ret = (exit_price * (1 - fee)) / (entry * (1 + fee)) - 1
        trades.append({**s, "entry": entry, "exit": exit_price, "exit_bar": exit_bar, "how": how,
                       "ret_pct": ret * 100, "r": (exit_price - entry) / (entry - stop),
                       "risk_pct": (1 - stop / entry) * 100, "reward_pct": (target / entry - 1) * 100})
        free_from = exit_bar
    return trades


def simulate_ladder(close, high, low, sigs: List[Dict], support_below) -> List[Dict]:
    """Hold while price climbs the ladder (owner, 2026-10-09: profit factor 1.31 and +1.7% a trade
    "does not make sense when the price made hundreds if not thousands of percents moves").
    No target: "targets up the ladder" - each day the stop rises to the highest support line under
    price (a broken resistance is support), never down; out when a low reaches it. `support_below(day,
    price)`: the highest line on that day's screen under `price`, or None."""
    trades, free_from, fee = [], -1, FEE_PCT / 100
    for s in sorted(sigs, key=lambda s: s["bar"]):
        d = s["bar"]
        if d <= free_from or d + 1 >= len(close) or not s["stop"] < close[d]:
            continue
        entry, stop, raised = close[d], s["stop"], []
        exit_bar, exit_price, how = len(close) - 1, None, "open at the end"
        for k in range(d + 1, len(close)):
            if low[k] <= stop:
                exit_bar, exit_price, how = k, stop, "stop"
                break
            up = support_below(k, close[k])
            if up is not None and up > stop:
                stop = up
                raised.append((k, up))
        if exit_price is None:
            exit_price = close[exit_bar]
        ret = (exit_price * (1 - fee)) / (entry * (1 + fee)) - 1
        trades.append({**s, "entry": entry, "exit": exit_price, "exit_bar": exit_bar, "how": how,
                       "ret_pct": ret * 100, "r": (exit_price - entry) / (entry - s["stop"]),
                       "risk_pct": (1 - s["stop"] / entry) * 100, "reward_pct": 0.0, "raised": raised,
                       "target": float("inf")})
        free_from = exit_bar
    return trades


def stats(trades: List[Dict]) -> Dict:
    if not trades:
        return {"trades": 0}
    r = np.array([t["ret_pct"] for t in trades])
    rr = np.array([t["r"] for t in trades])
    wins, losses = r[r > 0], r[r <= 0]
    return {"trades": len(trades), "win_rate": float(np.mean(r > 0) * 100), "avg_ret": float(r.mean()),
            "avg_r": float(rr.mean()), "profit_factor": float(wins.sum() / -losses.sum()) if losses.sum() < 0 else float("inf"),
            "compounded": float((np.prod(1 + r / 100) - 1) * 100),
            "avg_risk": float(np.mean([t["risk_pct"] for t in trades])),
            "avg_reward": float(np.mean([t["reward_pct"] for t in trades]))}
