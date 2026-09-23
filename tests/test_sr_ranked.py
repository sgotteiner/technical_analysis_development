"""
Tests for ranked S/R results — the playground shows MORE than one pipe / line per level (owner,
2026-09-22: "show more than 2 pairs, or single lines").
  ranked_pipes  the best pipe, then the next best whose lines are not used yet, and so on
                (Claude's reading: a line already shown is not shown again in a lower-ranked
                pipe, or the list fills with near-copies of pipe 1). Pipe 1 == find_pipe.
  ranked_lines  lines by line_key, one per key (same key = same first touch, last touch and
                count: near-identical lines). Line 1 == best_line.
Checked against a brute force over all pairs, under the default rules and changed ones.
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.sr_settings import SRRules, DEFAULT_RULES
from modules.shapes.sr_lines import candidate_lines, line_key, best_line, ranked_lines
from modules.shapes.sr_pipes import find_pipe, ranked_pipes, swing_legs

X = 0.10
RULE_SETS = [DEFAULT_RULES, SRRules(min_width_q=0.0), SRRules(max_width_mult=1.5, min_width_q=0.25),
             SRRules(max_divergence=0.002), SRRules(act_together=False, check_now=False),
             SRRules(both_sides=False, touch_pct=2.5)]


def _random(seed, n=300):
    c = 100 * np.exp(np.cumsum(np.random.default_rng(seed).normal(0, 0.03, n)))
    idx = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def _width_at(lo, up, x):
    return (up["y1"] + up["slope"] * (x - up["x1"])) - (lo["y1"] + lo["slope"] * (x - lo["x1"]))


def _valid(lo, up, legs, end, r):
    x0 = max(lo["x1"], up["x1"])
    lo_w = np.quantile(legs, r.min_width_q) if r.min_width_q > 0 else 0.0
    hi_w = r.max_width_mult * legs.max()
    w, w_now = _width_at(lo, up, x0), _width_at(lo, up, end)
    return ((not r.act_together or x0 < min(lo["last_touch"], up["last_touch"]))
            and up["slope"] - lo["slope"] <= r.max_divergence
            and w > 0 and w >= lo_w and w <= hi_w
            and (not r.check_now or 0 < w_now <= hi_w))


def _brute(df, end, period, r, k):
    lines = candidate_lines(df, end, period, X, rules=r)
    legs = swing_legs(df, end, period, X)
    if not len(legs):
        return []
    order = sorted(range(len(lines)), key=lambda i: line_key(lines[i]))
    rank = {i: p for p, i in enumerate(order)}
    pairs = [(lines[i]["touches"] + lines[j]["touches"], rank[i], rank[j], i, j)
             for i in range(len(lines)) for j in range(len(lines))
             if _valid(lines[i], lines[j], legs, end, r)]
    out, used = [], set()
    for *_, i, j in sorted(pairs, reverse=True):
        ki, kj = line_key(lines[i]), line_key(lines[j])
        if ki in used or kj in used or ki == kj:
            continue
        out.append((lines[i], lines[j])); used |= {ki, kj}
        if len(out) == k:
            break
    return out


@pytest.mark.parametrize("rules", RULE_SETS, ids=lambda r: str(r)[7:60])
@pytest.mark.parametrize("seed", [21, 24, 39])
def test_ranked_pipes_match_brute_force(seed, rules):
    df = _random(seed)
    assert ranked_pipes(df, 299, 250, X, k=4, rules=rules) == _brute(df, 299, 250, rules, 4)


@pytest.mark.parametrize("seed", [21, 22, 23, 43])
def test_first_ranked_pipe_is_find_pipe(seed):
    df = _random(seed)
    top = ranked_pipes(df, 299, 250, X, k=3)
    assert (top[0] if top else (None, None)) == find_pipe(df, 299, 250, X)


def test_ranked_pipes_share_no_line():
    df = _random(24)
    keys = [line_key(l) for pair in ranked_pipes(df, 299, 250, X, k=6, rules=SRRules(min_width_q=0.0)) for l in pair]
    assert len(keys) == len(set(keys)) >= 4


def test_pipe_search_stops_at_the_budget_and_says_so():
    """Pairs are checked in buckets of equal total touches, best first. When the budget runs out
    the result is marked incomplete, with the lowest total that was fully checked."""
    df = _random(24)
    info_full, info_part = {}, {}
    full = ranked_pipes(df, 299, 250, X, k=50, info=info_full)
    part = ranked_pipes(df, 299, 250, X, k=50, max_pairs=10, info=info_part)
    assert info_full["complete"] is True and info_part["complete"] is False
    assert info_part["checked_down_to"] > info_full["checked_down_to"]
    assert part == [p for p in full if p[0]["touches"] + p[1]["touches"] >= info_part["checked_down_to"]]


@pytest.mark.parametrize("seed", [8, 9, 10])
def test_ranked_lines_first_is_best_line_and_keys_are_distinct(seed):
    df = _random(seed)
    top = ranked_lines(df, 299, 250, X, k=8)
    assert top[0] == best_line(df, 299, 250, X)
    keys = [line_key(l) for l in top]
    assert keys == sorted(set(keys), reverse=True)
    all_keys = sorted({line_key(l) for l in candidate_lines(df, 299, 250, X)}, reverse=True)
    assert keys == all_keys[:8]
