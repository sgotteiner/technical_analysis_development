"""
Each trade read the way he reads a chart, in his units (owner, 2026-10-08: "i clicked the -8% trade.
you can see it was in a down trend and then pipe but didnt do enough to show it an uptrend in my
opinion. now i want you to analyze trades and try to explain in words what was wrong").

  the trend   from the trend LINES on the buy day only (zigzag_lines.direction): an unbroken down line over
              price - down; an up line under it - up; both - narrowing; none - no trend. "when you find the
              line you can see its slope why is there another direction algorithm" (owner, 2026-10-09)
  the line    what broke: a resistance level, the down trend line, or a broken up trend line coming back
  the retest  days after the breakout, and how far price got past the line before coming back
  the trade   stop and target distance, and after the buy the best it got before it ended

`faults` are the reasons a losing trade can be blamed on; the same checks on a winner show what it
had going for it. Nothing here decides a trade - it explains one.
"""
from typing import Dict, List
import numpy as np
from business_logic_services.zigzag_lines import direction_at

SAME_PCT = 1.5            # two peaks this close are "at one level" - the touch zone the lines use
SMALL_SHARE = 0.25        # a line under a quarter of the trend's size is small next to it - a stated guess


def _trend_words(d: Dict, day) -> str:
    """The trend by his rule, and its line as it stood on the buy day. A close beyond the line is its
    breakout - the trend goes on until 2 higher highs and 2 higher lows (or 2 lower) replace it."""
    if d["state"] not in ("up", "down"):
        return "no trend by the rule - neither 2 higher highs and higher lows nor 2 lower"
    t = d["down"] or d["up"]
    broke = (f"; price closed {'above' if t['down'] else 'below'} the line on {day(t['broken'])} - a breakout of it, "
             f"not the end of the trend" if t["broken"] is not None else "; the line held")
    return (f"{'DOWN' if t['down'] else 'up'} by the rule (no 2 {'higher' if t['down'] else 'lower'} highs and 2 "
            f"{'higher' if t['down'] else 'lower'} lows since it began); its line that day ran through "
            f"{day(t['points'][0])} {t['prices'][0]:,.0f} and {day(t['points'][1])} {t['prices'][1]:,.0f} "
            f"({np.expm1(t['slope']) * 100:+.2f}%/day){broke}")


def _strength_words(line: Dict) -> str:
    st = line.get("strength")
    if not st:
        return ""
    if line["kind"] == "trend":
        return f" (it carried a {st['size']:.0f}% move over {st['duration']} days, {st['touches']} points on it)"
    vs = f", {st['rel']:.2f}x the {st['trend_word']}'s {st['trend_size']:.0f}%" if st.get("rel") is not None else ""
    return f" ({st['touches']} zigzag point(s) on it, swing {st['size']:.1f}%{vs})"


def review(df, t: Dict, hist: Dict, size: float, cache: Dict) -> Dict:
    c, h = df["Close"].to_numpy(), df["High"].to_numpy()
    b, e, x = t["breakout_bar"], t["bar"], t["exit_bar"]
    day = lambda bar: df.index[int(bar)].strftime("%Y-%m-%d")
    big = direction_at(df, e, size, cache)                # the trend lines' direction that day
    line = t["line"]
    away = (max(h[b:e + 1]) / t["level"] - 1) * 100
    reward = None if t["target"] == float("inf") else (t["target"] / t["entry"] - 1) * 100
    best = (max(h[e + 1:x + 1]) / t["entry"] - 1) * 100 if x > e else 0.0
    rt = t.get("retest", {})
    retest_text = (f"The retest: the zigzag made a valley at {rt['price']:,.0f} in the line's zone, confirmed "
                   f"{e - b} day(s) after the breakout" if t.get("retest_kind") == "zigzag"
                   else f"The retest: a candle came back into the line's zone {e - b} day(s) after the breakout, low {rt.get('price', 0):,.0f}")
    place = None
    if reward is not None:
        place = (t["entry"] - t["stop"]) / (t["target"] - t["stop"])
    situation = (f"The trend: {_trend_words(big, day)}. "
                 + f"What broke: {line['role']} at {line['price']:,.0f}{_strength_words(line)}. "
                 + f"{retest_text}, after price got {away:.1f}% past the line. "
                 + f"Risk {t['risk_pct']:.1f}% to the stop, "
                 + (f"reward {reward:.1f}% to the target ({reward / t['risk_pct']:.2f} R)." if reward is not None else "no target above.")
                 + f" After the buy the best it got was {best:+.1f}% in {x - e} day(s).")
    faults: List[str] = []
    if big["state"] == "down":
        faults.append("it bought in a DOWN trend - a close above its line is not the end of the trend: it ends "
                      "with 2 higher highs and 2 higher lows (his rule)")
    elif big["state"] == "none":
        faults.append("no trend by the rule - nothing to ride")
    st = line.get("strength") or {}
    if line["kind"] == "level" and st.get("touches", 2) < 2:
        faults.append(f"the line it broke rested on ONE zigzag point - a weak line")
    if line["kind"] == "level" and st.get("rel") is not None and st["rel"] < SMALL_SHARE:
        faults.append(f"the line is small next to the trend: its swing {st['size']:.1f}% is {st['rel']:.2f}x "
                      f"the {st['trend_word']}'s {st['trend_size']:.0f}%")
    if "up trend line" in line["role"]:
        faults.append("the line it broke was a broken up-trend SUPPORT coming back, not a resistance")
    if t.get("retest_kind") != "zigzag" and e - b <= 2:
        faults.append(f"no real retest - a candle touched the zone {e - b} day(s) after the breakout, not a zigzag valley")
    if place is not None and 0.3 < place < 0.7:
        faults.append(f"it bought in the middle of the range - {t['risk_pct']:.1f}% above the support it stops at, "
                      f"{reward:.1f}% below the resistance it aims at")
    if reward is not None and reward < t["risk_pct"]:
        faults.append(f"risk {t['risk_pct']:.1f}% for {reward:.1f}% reward - less than 1 R")
    if t["how"] == "stop" and best < t["risk_pct"] / 2:
        faults.append(f"it never got going - the best was {best:+.1f}% before the stop")
    won = t["ret_pct"] > 0
    # the card titles it "why it worked" / "what went wrong": the text is only the reasons
    verdict = (("Even though: " + "; ".join(faults) + "." if faults else "Every check was in its favour.") if won
               else ("; ".join(faults) + "." if faults else "Nothing in these checks - the market turned.")).capitalize()
    return {"situation": situation, "verdict": verdict, "faults": faults, "trend": big["state"]}
