"""
The strategy's trades, for the page to draw (owner, 2026-10-08: "i wanna see trade entries and
exists"), each with what made it and, after it ended, what went right or wrong.

  entries  1. his breakout -> retest of a line on the zigzag (strategies/sr_breakout_strategy.py)
           2. a new higher low in an up trend by his counted rule (strategies/trend_entries.py)
  exit     no target: the stop rides up the zigzag's higher lows; out when a low reaches it
           (round 2026-10-09: +14% compounded selling at the next line -> +249% riding the trend)
"""
from typing import Dict, List
import pandas as pd
from business_logic_services.setup_history import setup_history
from business_logic_services.trade_review import review
from business_logic_services.trade_simulator import simulate_ladder, stats
from business_logic_services.zigzag_lines import _points
from business_logic_services.zigzag_lines import direction_at
from schemas.sr_view_schema import LinesConfig
from strategies.sr_breakout_strategy import RetestRules, signals
from strategies.trend_entries import higher_low_entries, last_higher_low

LINES = {"zigzag": LinesConfig(mode="zigzag", tol_pct=1.5)}


def _result(tr: Dict, day) -> str:
    raised = (f" The stop rose {len(tr['raised'])} time(s) with the higher lows: "
              + ", ".join(f"{p:,.0f} ({day(b)})" for b, p in tr["raised"]) + "." if tr["raised"] else " The stop never rose.")
    end = {"stop": "the stop was hit", "open at the end": "still open at the last candle"}[tr["how"]]
    return f"Out {day(tr['exit_bar'])} at {tr['exit']:,.0f} - {end}: {tr['ret_pct']:+.1f}% ({tr['r']:+.2f} R).{raised}"


def _higher_low_text(df, tr: Dict, cache: Dict, day) -> Dict:
    pts = _points(df, tr["bar"], 0.07, cache)
    best = (df["High"].iloc[tr["bar"] + 1:tr["exit_bar"] + 1].max() / tr["entry"] - 1) * 100 if tr["exit_bar"] > tr["bar"] else 0.0
    why = (f"In an up trend, the zigzag confirmed a new higher low on {day(tr['bar'])}: {tr['low']['price']:,.0f} "
           f"({day(tr['low']['bar'])}) above the one before, {tr['prev_low']['price']:,.0f} ({day(tr['prev_low']['bar'])}). "
           f"Bought at the close {tr['entry']:,.0f}, stop at that low (-{tr['risk_pct']:.1f}%), no target - it rides the trend.")
    faults = [] if tr["ret_pct"] > 0 else ([f"it never got going - the best was {best:+.1f}% before the stop"]
                                           if best < tr["risk_pct"] / 2 else ["the trend's higher low broke"])
    d = direction_at(df, tr["bar"], 0.07, cache)
    up = d["up"]
    return {"situation": f"The trend: up - the up trend line drawn {day(up['born'])} through the valleys "
                         f"{day(up['points'][0])} and {day(up['points'][1])} was unbroken under price. After the buy "
                         f"the best it got was {best:+.1f}% in {tr['exit_bar'] - tr['bar']} day(s).",
            "why": why, "faults": faults, "trend": d["state"],
            "verdict": ("; ".join(faults) + ".").capitalize() if faults else "It rode the up trend's higher lows."}


def trades_view(df: pd.DataFrame, mode: str, cache: Dict) -> Dict:
    key = ("trades", mode)
    if key in cache:
        return cache[key]
    c, h, l = (df[k].to_numpy() for k in ("Close", "High", "Low"))
    hist = setup_history(df, LINES[mode])
    t = df.index
    day = lambda b: t[int(b)].strftime("%Y-%m-%d")
    at = lambda d: _points(df, d, 0.07, cache)              # the zigzag known that day
    trend_at = lambda d: direction_at(df, d, 0.07, cache)["state"]   # the trend lines' direction that day
    # no breakout is bought while his counted trend is down: a close above a line is not the end of a
    # down trend (2026-10-09: "a trend is not over with a close above")
    entries = (signals(hist, c, h, l, RetestRules(retest="touch", trend="not_down"), at, trend_at)
               + higher_low_entries(sorted(hist), at, trend_at))
    out: List[Dict] = []
    for tr in simulate_ladder(c, h, l, entries, last_higher_low(at)):
        if tr.get("kind") == "higher low":
            words = _higher_low_text(df, tr, cache, day)
        else:
            rv = review(df, tr, hist, 0.07, cache)
            line = tr["line"]
            words = {**rv, "why": (f"{line['role']} at {line['price']:,.0f} broke on {day(tr['breakout_bar'])}; price came "
                                   f"back to it and held on {day(tr['bar'])}: bought at the close {tr['entry']:,.0f}. "
                                   f"Stop {tr['stop']:,.0f} (the line below, -{tr['risk_pct']:.1f}%), no target - "
                                   f"it rides the trend.")}
        out.append({"entry_bar": tr["bar"], "exit_bar": tr["exit_bar"], "breakout_bar": tr.get("breakout_bar", tr["bar"]),
                    "entry_time": int(t[tr["bar"]].timestamp()), "exit_time": int(t[tr["exit_bar"]].timestamp()),
                    "entry": tr["entry"], "exit": tr["exit"], "stop": tr["stop"], "target": None,
                    "how": "stop" if tr["how"] == "stop" else "time", "ret_pct": tr["ret_pct"], "r": tr["r"],
                    "risk_pct": tr["risk_pct"], "kind": tr.get("kind", "breakout -> retest"),
                    "situation": words["situation"], "verdict": words["verdict"], "faults": words["faults"],
                    "trend": words["trend"], "why": words["why"], "result": _result(tr, day)})
    res = {"trades": out, "stats": stats([{"ret_pct": x["ret_pct"], "r": x["r"], "risk_pct": x["risk_pct"],
                                            "reward_pct": 0.0} for x in out])}
    cache[key] = res
    return res
