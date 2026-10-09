"""
Backtest his strategy - breakout of a resistance on his setup, buy the retest of THAT line - on BTC
daily, with the lines his page drew on each day (business_logic_services/setup_history.py), against
buying on any day between the same lines with the same stop and target.

Usage:  python scripts/backtest_sr_breakout.py
"""
import os
import sys
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from business_logic_services.setup_history import PAGE, setup_history
from schemas.sr_view_schema import LinesConfig
from business_logic_services.zigzag_lines import _points
from business_logic_services.trade_simulator import simulate, stats
from scripts.sr_playground import load_daily
from strategies.sr_breakout_strategy import RetestRules, _price, signals

SPLIT = "2023-01-01"                               # fitted before, judged after


def any_day(hist, close):
    """Every day, between the lines on his screen: stop at the line below price, target at the one above."""
    out = []
    for d, day in hist.items():
        p = [_price(l, d, d) for l in day["lines"]]
        below, above = [x for x in p if x < close[d]], [x for x in p if x > close[d]]
        if below and above:
            out.append({"bar": d, "stop": max(below), "target": min(above), "why": "any day"})
    return out


def table(df, trades):
    split = int(df.index.searchsorted(pd.Timestamp(SPLIT, tz="UTC")))
    return {"2018-2022": stats([t for t in trades if t["bar"] < split]),
            "2023-2026": stats([t for t in trades if t["bar"] >= split])}


def line(name, res):
    def cell(s):
        if not s.get("trades"):
            return "no trades".ljust(52)
        return (f"{s['trades']:4} tr  win {s['win_rate']:3.0f}%  avg {s['avg_ret']:+5.1f}%  {s['avg_r']:+.2f}R  "
                f"PF {s['profit_factor']:4.2f}")
    print(f"{name:44} | {cell(res['2018-2022'])} | {cell(res['2023-2026'])}")


def main():
    df = load_daily()
    c, h, l = (df[k].to_numpy() for k in ("Close", "High", "Low"))
    cache = {}
    at = lambda d: _points(df, d, 0.07, cache)
    report(df, c, h, l, setup_history(df, LinesConfig(mode="zigzag", tol_pct=1.5)), "lines: from the zigzag, kept", at)


def report(df, c, h, l, hist, title, at):
    print()
    print(f"{title:44} | {'2018-2022':52} | {'2023-2026':52}")
    variants = [(f"{rt:5} | trend {tr:8} | {'strong lines' if sh else 'all lines'}",
                 RetestRules(retest=rt, trend=tr, min_share=sh))
                for rt in ("touch", "hold", "zigzag") for tr in ("any", "not_down", "up") for sh in (0.0, 0.25)]
    for name, rules in variants:
        line(name, table(df, simulate(c, h, l, signals(hist, c, h, l, rules, at))))
    line("any day, same lines, stop and target", table(df, simulate(c, h, l, any_day(hist, c), overlap=True)))


if __name__ == "__main__":
    main()
