"""
Tests for the playground view (business_logic_services/sr_playground_service.py): what the
page draws for one "now" and one set of settings — per level, ranked pipes and single lines.
It must agree with the shape blocks and use only candles up to "now".
"""
import numpy as np
import pandas as pd
from business_logic_services.sr_playground_service import playground_view
from modules.shapes.sr_settings import DEFAULT_LEVELS, DEFAULT_RULES, SRRules
from modules.shapes.sr_pipes import sr_lines_at, ranked_pipes, pipe_width
from modules.shapes.sr_lines import ranked_lines


def _random(seed, n=460):
    c = 100 * np.exp(np.cumsum(np.random.default_rng(seed).normal(0, 0.03, n)))
    idx = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def test_default_view_is_the_four_lines():
    df = _random(40)
    view = playground_view(df, 459, DEFAULT_LEVELS, DEFAULT_RULES, pairs=1, singles=0)
    four = sr_lines_at(df, 459)
    for lvl in DEFAULT_LEVELS:
        pipes = view["levels"][lvl]["pipes"]
        if four[f"{lvl}_support"] is None:
            assert pipes == []
        else:
            assert pipes[0]["support"] == four[f"{lvl}_support"] and pipes[0]["resistance"] == four[f"{lvl}_resistance"]
            assert pipes[0]["width"] == pipe_width(four[f"{lvl}_support"], four[f"{lvl}_resistance"])
        assert view["levels"][lvl]["lines"] == []


def test_view_carries_ranked_pipes_lines_and_swings_for_any_levels():
    df = _random(41)
    levels = {"small": {"period": 120, "magnitude": 0.08}, "mid": {"period": 250, "magnitude": 0.12}}
    rules = SRRules(min_width_q=0.0, candidate_ratio=0.75)
    view = playground_view(df, 459, levels, rules, pairs=3, singles=5)
    assert list(view["levels"]) == ["small", "mid"] and view["end"] == 459
    for lvl, cfg in levels.items():
        got = view["levels"][lvl]
        want = ranked_pipes(df, 459, cfg["period"], cfg["magnitude"], k=3, rules=rules)
        assert [(p["support"], p["resistance"]) for p in got["pipes"]] == want
        assert got["lines"] == ranked_lines(df, 459, cfg["period"], cfg["magnitude"], k=5, rules=rules)
        assert got["complete"] is True
        assert got["largest_swing"] >= got["median_swing"] > 0


def test_view_uses_only_candles_up_to_now():
    df = _random(42)
    rules = SRRules(both_sides=False, max_width_mult=1.3)
    for end in (430, 445, 458):
        full = playground_view(df, end, DEFAULT_LEVELS, rules, pairs=3, singles=4)
        cut = playground_view(df.iloc[:end + 1], end, DEFAULT_LEVELS, rules, pairs=3, singles=4)
        assert full == cut, end


def test_turning_point_cache_does_not_change_the_answer():
    df = _random(43)
    cache = {}
    for end in (440, 459):
        assert playground_view(df, end, DEFAULT_LEVELS, DEFAULT_RULES, 2, 2, cache=cache) == \
            playground_view(df, end, DEFAULT_LEVELS, DEFAULT_RULES, 2, 2)
