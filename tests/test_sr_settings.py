"""
Tests for the S/R rule settings (modules/shapes/sr_settings.py) and their effect on lines.
The playground (owner, 2026-09-22) must let the owner change every rule and see the result, so
each rule that used to be a constant is now a setting. Defaults = the rules as they were (the
39 older tests run on the defaults and must not change).
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.sr_settings import SRRules, DEFAULT_RULES, DEFAULT_LEVELS, parse_levels, parse_rules
from modules.shapes.sr_lines import candidate_lines, level_points, TOUCH_TOL, line_key
from modules.shapes.sr_turning_points import turning_points

X = 0.10


def _df(close):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2022-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def _channel(n=200, width=np.log(1.2), leg=12, base=100.0):
    t = np.arange(n)
    tri = np.abs((t % (2 * leg)) - leg) / leg
    return np.exp(np.log(base) + width * (1 - tri))


def _random(seed, n=300):
    return _df(100 * np.exp(np.cumsum(np.random.default_rng(seed).normal(0, 0.03, n))))


def test_defaults_are_the_rules_as_they_were():
    r = DEFAULT_RULES
    assert (r.touch_pct, r.candidate_ratio, r.both_sides, r.min_touches) == (1.5, 0.5, True, 2)
    assert (r.max_divergence, r.min_width_q, r.max_width_mult, r.act_together, r.check_now) == (0.0, 0.5, 1.0, True, True)
    assert r.tol == pytest.approx(TOUCH_TOL)
    assert DEFAULT_LEVELS == {"higher": {"period": 400, "magnitude": 0.20}, "lower": {"period": 100, "magnitude": 0.10}}


def test_parse_rules_fills_defaults_and_rejects_nonsense():
    assert parse_rules({}) == DEFAULT_RULES
    assert parse_rules({"touch_pct": 3, "both_sides": False}) == SRRules(touch_pct=3.0, both_sides=False)
    for bad in ({"touch_pct": -1}, {"candidate_ratio": 0}, {"candidate_ratio": 1.5}, {"min_touches": 1},
                {"min_width_q": 1.2}, {"max_width_mult": 0}, {"max_divergence": -0.1}, {"nope": 1}):
        with pytest.raises(ValueError):
            parse_rules(bad)


def test_parse_levels_accepts_any_number_of_levels_and_rejects_nonsense():
    lv = parse_levels({"a": {"period": 50, "magnitude": 0.05}, "b": {"period": 200, "magnitude": 0.15},
                       "c": {"period": 800, "magnitude": 0.3}})
    assert list(lv) == ["a", "b", "c"] and lv["a"] == {"period": 50, "magnitude": 0.05}
    for bad in ({}, {"a": {"period": 1, "magnitude": 0.1}}, {"a": {"period": 100, "magnitude": 0}},
                {"a": {"period": 100}}, {"": {"period": 100, "magnitude": 0.1}}):
        with pytest.raises(ValueError):
            parse_levels(bad)


def test_candidate_ratio_sets_the_candidate_zigzag():
    df = _random(1)
    for ratio in (0.5, 0.75, 1.0):
        pts, _ = level_points(df, 299, 250, X, rules=SRRules(candidate_ratio=ratio))
        tp = turning_points(df, X * ratio)
        keep = tp["conf"] <= 299
        assert list(pts["idx"]) == list(tp["idx"][keep])


def test_wider_touch_tolerance_catches_an_overshooting_peak():
    close = _channel()
    close[12 + 24 * 3] *= 1.03                                    # one peak pokes 3% above 120
    df = _df(close)
    flat_120 = lambda rules: [l for l in candidate_lines(df, 199, 200, X, rules=rules)
                              if l["slope"] == 0.0 and abs(l["y1"] - np.log(120)) < 1e-9]
    tight, loose = flat_120(DEFAULT_RULES), flat_120(SRRules(touch_pct=4.0))
    assert max(l["touches"] for l in loose) == max(l["touches"] for l in tight) + 1


def test_min_touches_filters_lines():
    df = _random(2)
    two, three = candidate_lines(df, 299, 250, X), candidate_lines(df, 299, 250, X, rules=SRRules(min_touches=3))
    assert three and all(l["touches"] >= 3 for l in three)
    assert sorted(map(line_key, three)) == sorted(line_key(l) for l in two if l["touches"] >= 3)


@pytest.mark.parametrize("seed", [3, 4, 5])
def test_one_side_significance_only_adds_touches(seed):
    """With one far side enough, every line has at least the touches it had with both sides."""
    df = _random(seed)
    both = candidate_lines(df, 299, 250, X)
    ident = lambda l: (round(l["slope"], 12), round(l["y1"] - l["slope"] * l["x1"], 9))
    one = {ident(l): l["touches"] for l in candidate_lines(df, 299, 250, X, rules=SRRules(both_sides=False))}
    assert len(one) >= len(both)
    for l in both:
        assert one[ident(l)] >= l["touches"]


def _path(points, bars=6):
    """Close prices along straight (log) legs between the given turning prices."""
    legs = [np.linspace(np.log(a), np.log(b), bars, endpoint=False) for a, b in zip(points, points[1:])]
    return np.exp(np.concatenate(legs + [[np.log(points[-1])]]))


def _flat_100_touches(df, period, rules=DEFAULT_RULES):
    lines = [l for l in candidate_lines(df, len(df) - 1, period, X, rules=rules)
             if abs(l["slope"]) < 1e-12 and abs(l["y1"] - np.log(100)) < 1e-9]
    return max((l["touches"] for l in lines), default=0)


def test_touch_at_the_window_start_is_judged_by_the_neighbour_before_the_window():
    """Peaks on 100; the first one in the window came from a valley at 93 (outside the window),
    only 7% away, so it is not a significant touch. The other three came from 85: significant."""
    close = _path([120, 93, 100, 85, 100, 85, 100, 85, 100, 80])
    first_peak = 6 * 2                                            # bar of the first 100
    assert _flat_100_touches(_df(close), period=len(close) - first_peak) == 3


def test_one_side_mode_never_counts_an_unknown_neighbour_as_far():
    """The first turning point of the data (peak on 100) has no known point before it, and the
    valley after it is only 7% away: not significant even when one far side is enough."""
    close = _path([80, 100, 93, 100, 85, 100, 85, 100, 80])
    assert _flat_100_touches(_df(close), period=len(close), rules=SRRules(both_sides=False)) == 3
