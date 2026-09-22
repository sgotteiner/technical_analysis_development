"""
Tests for S/R pipes (modules/shapes/sr_pipes.py): each level's lower and upper line chosen together.
Owner rules (2026-09-22): not a widening shape; not too wide (<= largest swing move); not
really narrow (Claude's bound: >= median swing move); channels AND triangles are pipes.
Also: both lines act at the same time (touch periods overlap) and the rules hold at "now"
(a triangle past its apex opens up the other way = widening).
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.sr_lines import candidate_lines, line_key
from modules.shapes.sr_pipes import find_pipe, sr_lines_at, swing_legs, pipe_width, LEVELS

X = 0.10


def _df(close):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2022-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def _pipe(n, low_slope, up_slope, width0, leg=12, base=100.0):
    """Zigzag: valleys on the lower line, peaks on the upper line (log)."""
    t = np.arange(n)
    tri = np.abs((t % (2 * leg)) - leg) / leg
    lower = np.log(base) + low_slope * t
    upper = np.log(base) + width0 + up_slope * t
    return np.exp(lower + (upper - lower) * (1 - tri))


def _random(seed, n=300):
    return _df(100 * np.exp(np.cumsum(np.random.default_rng(seed).normal(0, 0.03, n))))


def _width_at(lo, up, x):
    return (up["y1"] + up["slope"] * (x - up["x1"])) - (lo["y1"] + lo["slope"] * (x - lo["x1"]))


def _check_rules(df, end, lo, up, period, magnitude):
    legs = swing_legs(df, end, period, magnitude)
    x0 = max(lo["x1"], up["x1"])
    assert x0 < min(lo["last_touch"], up["last_touch"])                  # act together
    assert up["slope"] - lo["slope"] <= 1e-12                             # never widens
    assert np.median(legs) - 1e-9 <= _width_at(lo, up, x0) <= legs.max() + 1e-9
    assert 0 < _width_at(lo, up, end) <= legs.max() + 1e-9                # apex not passed at now


def test_swing_legs_measure_the_magnitude_zigzag():
    close = [100, 90, 80, 90, 100, 110, 100, 90, 95, 100, 120, 110, 100]
    legs = swing_legs(_df(close), end=12, period=13, magnitude=0.10)
    # 100 only anchors the start; 80 (valley), 110 (peak), 90 (valley), 120 (peak, confirmed by
    # the drop to 100 on the last bar)
    assert legs == pytest.approx(np.abs(np.diff(np.log([80, 110, 90, 120]))))


@pytest.mark.parametrize("slope", [0.0, 0.004, -0.004])
def test_rotated_channel_gives_the_same_pipe(slope):
    df = _df(_pipe(200, slope, slope, np.log(1.2)))
    lo, up = find_pipe(df, end=199, period=200, magnitude=X)
    assert lo["slope"] == pytest.approx(slope, abs=1e-9) and up["slope"] == pytest.approx(slope, abs=1e-9)
    assert _width_at(lo, up, 199) == pytest.approx(np.log(1.2), abs=1e-9)


def test_triangle_is_a_pipe():
    df = _df(_pipe(200, 0.001, -0.001, np.log(1.6)))
    lo, up = find_pipe(df, end=199, period=200, magnitude=X)
    assert lo["slope"] == pytest.approx(0.001, abs=1e-9) and up["slope"] == pytest.approx(-0.001, abs=1e-9)


def test_widening_shape_is_never_a_pipe():
    df = _df(_pipe(200, -0.001, 0.001, np.log(1.25)))
    lo, up = find_pipe(df, end=199, period=200, magnitude=X)
    assert lo is None or up["slope"] - lo["slope"] <= 1e-12


def test_triangle_past_its_apex_is_not_a_pipe():
    tri = _pipe(150, 0.0015, -0.0015, np.log(1.5))                 # lines cross at bar ~135
    df = _df(np.concatenate([tri, np.full(40, tri[-1])]))
    end = len(df) - 1
    lo, up = find_pipe(df, end, period=len(df), magnitude=X)
    assert lo is None or _width_at(lo, up, end) > 0


@pytest.mark.parametrize("seed", range(6))
def test_every_returned_pipe_obeys_the_rules(seed):
    df = _random(seed, n=460)
    lines = sr_lines_at(df, end=459)
    for lvl, cfg in LEVELS.items():
        lo, up = lines[f"{lvl}_support"], lines[f"{lvl}_resistance"]
        assert (lo is None) == (up is None)
        if lo:
            _check_rules(df, 459, lo, up, cfg["period"], cfg["magnitude"])


@pytest.mark.parametrize("seed", [21, 22, 23, 24, 25, 26, 39, 43])   # 39, 43: the too-wide rule decides
def test_pipe_matches_brute_force_over_all_pairs(seed):
    df = _random(seed)
    end, period = 299, 250
    lines = candidate_lines(df, end, period, X)
    legs = swing_legs(df, end, period, X)
    best = None
    for lo in lines:
        for up in lines:
            x0 = max(lo["x1"], up["x1"])
            if not x0 < min(lo["last_touch"], up["last_touch"]) or up["slope"] > lo["slope"]:
                continue
            if not (np.median(legs) <= _width_at(lo, up, x0) <= legs.max() and 0 < _width_at(lo, up, end) <= legs.max()):
                continue
            key = (lo["touches"] + up["touches"], line_key(lo), line_key(up))
            best = key if best is None or key > best else best
    lo, up = find_pipe(df, end, period, X)
    assert (None if lo is None else (lo["touches"] + up["touches"], line_key(lo), line_key(up))) == best


def test_no_lookahead_live_replay():
    df = _random(31, n=460)
    for end in range(420, 459, 6):
        assert sr_lines_at(df, end) == sr_lines_at(df.iloc[:end + 1], end), end


def test_scale_invariance():
    df = _random(32, n=460)
    a, b = sr_lines_at(df, 459), sr_lines_at(df * 5, 459)
    for key in a:
        assert (a[key] is None) == (b[key] is None)
        if a[key]:
            assert line_key(a[key]) == line_key(b[key]) and a[key]["slope"] == pytest.approx(b[key]["slope"])
