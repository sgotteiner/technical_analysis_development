"""
Tests for the "strong resistance + bull flag" setup detector (modules/setups/resistance_flag.py).
Owner's setup (2026-09-22): a strong resistance that stopped price last time, and a bullish
pattern (a bull flag) running into it; the trade is the breakout (maybe after a retest).
Detected at bar `end`: a bull flag ends at `end` and its high is within `near` of a strong
resistance line whose last peak came before the pole. `broken` = the close at `end` is above the line.
"""
import numpy as np
import pytest
from modules.setups.resistance_flag import setup_at, scan, episodes
from setup_charts import df_from_close, legs, setup_chart, REJECT_THEN_FLAG


def test_finds_the_setup():
    df = setup_chart()
    s = setup_at(df, len(df) - 1)
    assert s is not None
    assert abs(s["resistance"]["slope"]) < 1e-12 and s["resistance"]["y1"] == pytest.approx(np.log(100))
    assert s["flag"]["pole_start"] == 115 and s["flag"]["flag_high"] == pytest.approx(98)
    assert s["gap"] == pytest.approx(np.log(98 / 100)) and s["broken"] is False


def test_a_flag_far_below_the_resistance_is_not_the_setup():
    moves = REJECT_THEN_FLAG[:4] + [(55, 20), (55, 5), (72, 5), (69, 3), (73, 3), (70, 3)]     # flag near 73
    df = setup_chart(moves)
    assert setup_at(df, len(df) - 1) is None


def test_no_rejection_means_no_setup():
    df = df_from_close(legs(60, [(100, 30), (70, 20), (100, 20), (89, 20), (89, 25), (95, 5), (91, 3), (96, 3), (92, 2), (98, 3), (95, 2)]))
    assert setup_at(df, len(df) - 1) is None


def test_a_close_above_the_line_is_marked_broken():
    """2.5% above the line: past the resistance's own break tolerance, but a close inside the flag
    is the breakout, not a reason to drop the line (the line is judged up to the pole's start)."""
    df = setup_chart(REJECT_THEN_FLAG + [(102.5, 1)])
    s = setup_at(df, len(df) - 1)
    assert s is not None and s["broken"] is True


def test_episodes_split_at_a_gap():
    found = [{"end": 5}, {"end": 6}, {"end": 9}]
    assert [(e["first"], e["last"], e["days"]) for e in episodes(found)] == [(5, 6, 2), (9, 9, 1)]


def test_scan_uses_only_the_past_and_episodes_merge_days():
    df = setup_chart()
    found = scan(df)
    assert found and found[-1]["end"] == len(df) - 1
    for s in found:
        assert s == setup_at(df.iloc[:s["end"] + 1], s["end"])
    eps = episodes(found)
    assert all(e["days"] == e["last"] - e["first"] + 1 for e in eps)          # runs of consecutive bars
    assert sum(e["days"] for e in eps) == len(found)
    assert eps[-1]["setup"] == found[-1]
