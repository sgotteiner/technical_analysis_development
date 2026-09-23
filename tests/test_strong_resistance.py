"""
Tests for strong resistance lines (modules/shapes/strong_resistance.py), from the owner's setup:
"strong resistance that stopped it the previous time it reached there".
A line through two major peaks (10% zigzag, confirmed by `end`); strong when price fell far after
its last peak; still resistance when no close went clearly above it before the new approach.
"""
import numpy as np
import pytest
from modules.shapes.strong_resistance import resistance_lines, RESISTANCE
from setup_charts import df_from_close, legs, setup_chart

APPROACH = 115         # bar where the new rise (the pole) starts in setup_chart()


def test_line_through_the_two_rejected_peaks():
    df = setup_chart()
    lines = resistance_lines(df, len(df) - 1, before=APPROACH)
    flat = [l for l in lines if abs(l["slope"]) < 1e-12 and abs(l["y1"] - np.log(100)) < 1e-9]
    assert flat, lines
    l = flat[0]
    assert (l["x1"], l["last_peak"]) == (30, 70)
    assert l["rejection"] == pytest.approx(np.log(100 / 70))


def test_a_close_above_the_line_before_the_approach_kills_it():
    df = df_from_close(legs(60, [(100, 30), (70, 20), (100, 20), (70, 20), (106, 8), (70, 17), (95, 5), (93, 5)]))
    assert not [l for l in resistance_lines(df, len(df) - 1, before=len(df) - 11)
                if abs(l["slope"]) < 1e-12 and abs(l["y1"] - np.log(100)) < 1e-9]


def test_a_weak_rejection_is_not_strong():
    df = df_from_close(legs(60, [(100, 30), (70, 20), (100, 20), (88, 20), (88, 25), (97, 5), (95, 5)]))
    assert not [l for l in resistance_lines(df, len(df) - 1, before=95) if abs(l["slope"]) < 1e-12]


def test_only_confirmed_peaks_are_used():
    df = setup_chart()
    # at bar 75 the second peak (bar 70) has fallen only 8.5%, not the 10% that makes it a known
    # peak — even when a smaller rejection (5%) would be enough for the line
    p = {**RESISTANCE, "min_rejection": 0.05}
    assert all(l["last_peak"] < 70 for l in resistance_lines(df, 75, before=75, p=p))


def test_peaks_from_the_new_approach_are_not_touches():
    """A major peak on the line after `before` belongs to the new approach, not to the resistance."""
    df = df_from_close(legs(60, [(100, 30), (70, 20), (100, 20), (70, 20), (100, 10), (80, 10), (82, 5)]))
    lines = resistance_lines(df, len(df) - 1, before=90)
    flat = [l for l in lines if abs(l["slope"]) < 1e-12 and abs(l["y1"] - np.log(100)) < 1e-9]
    assert flat and flat[0]["touches"] == 2


def test_no_lookahead():
    rng = np.random.default_rng(5)
    df = df_from_close(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 500))), wick=0.01)
    for end in range(420, 500, 9):
        assert resistance_lines(df, end, before=end - 10) == resistance_lines(df.iloc[:end + 1], end, before=end - 10)
