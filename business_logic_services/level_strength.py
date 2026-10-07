"""
How strong a level is: how likely price is to TURN at it the next time it gets there.

His ideas (owner, 2026-10-07): "maybe we could add strength based on how close it is ... how about
accounting for the move afterwards? ... a support that held a long time is stronger ... lines used a
lot as support and resistance ... i would say they are weak ... closer or more resilient or a
strength score based on both?" - and "i offer ideas you do the algorithm".

Each idea became a feature and was MEASURED, not weighted by hand: every level within the move's
reach, sampled weekly 2018-06 -> 2026-07 (2,419 levels), features from data up to that date only,
outcome = did price turn at the next visit (a touch) or go through (a break). Base rate 50.3%.
Alone, each feature is weak (AUC 0.46-0.54): recent, long-lived and a big move afterwards each help
a little; levels broken before turned slightly MORE often, the classic flip - not less.
Together, fitted on 2018-2022 and tested on 2023-2026: AUC 0.568; the top quarter turned 61% of the
time, the other three quarters 47-48%. So the score separates the strong quarter from the rest and
does no more than that - which is what the label says.

The weights below are that 2018-2022 fit. They are used for every date, which makes dates before
2023 in-sample: fine for a label on the chart, not for a backtest.
"""
from typing import Dict, List
import numpy as np
from modules.shapes.swing_moves import leg_moves
from modules.shapes.touch_zones import touch_zones

FEATURES = ("age_log", "span_log", "visits", "held", "broken", "held_share", "reaction")
MEAN = (4.1099, 5.3495, 3.6961, 3.6105, 3.3678, 0.5169, 1.7266)
SCALE = (1.5016, 1.3454, 1.5607, 2.1326, 2.1783, 0.1314, 0.7979)
WEIGHT = (-0.1245, 0.0407, -0.0180, 0.1096, -0.1399, -0.3002, 0.0993)
INTERCEPT = -0.0092
STRONG_FROM = 0.5343       # the top quarter of the 2018-2022 scores
TURNED = {"strong": 61, "ordinary": 48}      # % that turned at the next visit, 2023-2026
TOUCH_PCT = 1.4            # the touch-zone tolerance the page draws with; the study used the same
MEDIAN_REACTION = 1.4601   # stands in when none of a level's dots has a leg out yet


def _features(level: Dict, end: int, high, low, out_by_bar: Dict[int, float], yard: float):
    dots = [int(b) for b in level.get("points", [])]
    past = touch_zones(level["price"], TOUCH_PCT, high, low, end)
    held = sum(z["kind"] == "touch" for z in past)
    broken = sum(z["kind"] == "break" for z in past)
    outs = [out_by_bar[b] for b in dots if b in out_by_bar and np.isfinite(out_by_bar[b])]
    reaction = float(np.mean(outs)) / yard if outs and yard > 0 else MEDIAN_REACTION
    # as the study measured them: the band's own first and last visit and its visit count
    first, last = level.get("first", min(dots, default=end)), level.get("last", max(dots, default=end))
    return (np.log1p(max(end - last, 0)), np.log1p(max(last - first, 0)), level.get("visits", len(dots)),
            held, broken, (held + 1) / (held + broken + 2), reaction)


def score(features) -> float:
    z = sum(w * (f - m) / s for f, m, s, w in zip(features, MEAN, SCALE, WEIGHT)) + INTERCEPT
    return float(1 / (1 + np.exp(-z)))


def add_strength(levels: List[Dict], tp: Dict, high, low, end: int, yard: float) -> List[Dict]:
    """Each level, with how likely price is to turn at it and the label that says so."""
    known = np.flatnonzero((tp["conf"] <= end) & (tp["idx"] <= end))
    legs = leg_moves(tp, high, low)[known]
    out_by_bar = {int(b): float(o) for b, o in zip(tp["idx"][known][:-1], legs[1:])}   # the leg OUT
    out = []
    for lv in levels:
        f = _features(lv, end, high, low, out_by_bar, yard)
        p = score(f)
        label = "strong" if p >= STRONG_FROM else "ordinary"
        # held and broken shown, not only folded into the score: "dont count only how many times
        # they were respected but also broken" (owner, 2026-10-07)
        out.append({**lv, "strength": p, "strength_label": label, "held": int(f[3]), "broken": int(f[4])})
    return out
