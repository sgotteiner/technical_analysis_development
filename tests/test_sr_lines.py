"""
Tests for S/R lines (modules/shapes/sr_lines.py). Owner's definition (2026-09-22):
  a line runs through / close to the MOST significant peaks and valleys - it shows the trend.
  It may sit inside the graph and touch both peaks and valleys (split the graph); a small
  overshoot does not move it. A touch is significant if price moved >= X away FROM THE LINE
  (measured against the line, so a rotated pipe counts the same as a flat one) - on both sides
  of the touch where both neighbours are known (Claude's reading: with one side only, a steep
  line gets a far neighbour for free).
Ground truth here is built in: synthetic charts are generated from known lines.
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.sr_lines import best_line, candidate_lines, line_key, TOUCH_TOL
from modules.shapes.sr_turning_points import turning_points, PEAK

X = 0.10


def _df(close):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2022-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c}, index=idx)


def _channel(n=200, slope=0.0, width=np.log(1.2), leg=12, base=100.0):
    """Zigzag whose valleys lie on support = log(base) + slope*t and peaks on support + width."""
    t = np.arange(n)
    tri = np.abs((t % (2 * leg)) - leg) / leg                  # 1 at t=0 mod 24 ... 0 at 12
    return np.exp(np.log(base) + slope * t + width * (1 - tri))


def _value_at(line, x):
    return line["y1"] + line["slope"] * (x - line["x1"])


@pytest.mark.parametrize("slope", [0.0, 0.004, -0.004])
def test_rotated_channel_scores_the_same(slope):
    """Same pipe, rotated: the best line has the pipe's slope and the same number of touches."""
    flat = best_line(_df(_channel(slope=0.0)), end=199, period=200, magnitude=X)
    line = best_line(_df(_channel(slope=slope)), end=199, period=200, magnitude=X)
    assert line["slope"] == pytest.approx(slope, abs=1e-9)
    assert line["touches"] == flat["touches"] >= 6


def test_small_overshoot_does_not_move_the_line():
    close = _channel(slope=0.0)
    close[12 + 24 * 3] *= 1.03                                  # one peak pokes 3% above resistance
    df = _df(close)
    res = [l for l in candidate_lines(df, end=199, period=200, magnitude=X) if l["slope"] == 0.0
           and abs(l["y1"] - np.log(120)) < 1e-9]
    assert res, "the 120 resistance line must still exist"
    best = best_line(df, end=199, period=200, magnitude=X)
    assert best["slope"] == pytest.approx(0.0, abs=1e-12)       # still the flat channel lines


def test_line_can_split_the_graph_touching_peaks_and_valleys():
    """Level 100: support for three bounces, then (after a breakdown) resistance for three."""
    up = [100, 108, 116, 108, 100]                              # valley on 100, bounce 16%
    down = [100, 93, 86, 93, 100]                               # peak on 100, drop 14%
    close = np.array((up[:-1] * 3) + [100, 94, 88, 82] + (down[:-1] * 3) + [100, 90, 80], dtype=float)
    df = _df(close)
    line = best_line(df, end=len(df) - 1, period=len(df), magnitude=X)
    assert line["slope"] == pytest.approx(0.0, abs=1e-12)
    assert _value_at(line, 0) == pytest.approx(np.log(100), abs=1e-9)
    tp = turning_points(df, X / 2)
    on_line = np.abs(tp["y"] - np.log(100)) <= TOUCH_TOL
    assert set(tp["kind"][on_line]) == {PEAK, -PEAK}              # touched from both sides


def test_swings_smaller_than_the_magnitude_give_no_line():
    close = _channel(width=np.log(1.07))                        # 7% swings: turning points, not significant
    assert best_line(_df(close), end=199, period=200, magnitude=X) is None


def test_matches_slow_reference_implementation():
    rng = np.random.default_rng(8)
    df = _df(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 300))))
    end, period = 299, 250
    tp = turning_points(df, X / 2)
    keep = [k for k in range(len(tp["idx"])) if tp["conf"][k] <= end]
    inside = [k for k in keep if tp["idx"][k] >= end - period + 1]
    best = None
    for i in inside:
        for j in inside:
            if tp["idx"][j] <= tp["idx"][i]:
                continue
            slope = (tp["y"][j] - tp["y"][i]) / (tp["idx"][j] - tp["idx"][i])
            L = lambda x: tp["y"][i] + slope * (x - tp["idx"][i])
            sig = []
            for k in inside:
                if abs(tp["y"][k] - L(tp["idx"][k])) > TOUCH_TOL:
                    continue
                side = 1 if tp["kind"][k] == PEAK else -1          # neighbours lie on the other side
                gaps = [side * (L(tp["idx"][n]) - tp["y"][n]) for n in (k - 1, k + 1) if n in keep]
                if gaps and min(gaps) >= np.log(1 + X):          # far on BOTH sides (where known)
                    sig.append(tp["idx"][k])
            if len(sig) >= 2:
                key = (len(sig), max(sig), -min(sig))
                best = key if best is None or key > best else best
    got = best_line(df, end, period, X)
    assert (None if got is None else line_key(got)) == best


def test_huge_candle_that_is_both_peak_and_valley_is_handled():
    """One bar with a +-12% range spans the threshold on its own. It must not become a peak and a
    valley on the same day (one candle cannot be both - the bar does not say which came first), and
    no line may come out with an infinite slope."""
    close = _channel(slope=0.0)
    df = _df(close)
    big = 12 * 5 + 6
    df.iloc[big, df.columns.get_loc("High")] = close[big] * 1.12
    df.iloc[big, df.columns.get_loc("Low")] = close[big] * 0.88
    tp = turning_points(df, X / 2)
    assert (np.diff(tp["idx"]) > 0).all(), "never two turning points on one bar"
    assert (tp["conf"] > tp["idx"]).all(), "an extreme is confirmed by a later bar, not its own"
    with np.errstate(divide="raise", invalid="raise"):
        lines = candidate_lines(df, end=199, period=200, magnitude=X)
    assert all(np.isfinite(l["slope"]) for l in lines)


def test_no_lookahead_live_replay():
    rng = np.random.default_rng(9)
    df = _df(100 * np.exp(np.cumsum(rng.normal(0, 0.03, 260))))
    for end in range(150, 259, 9):
        assert best_line(df, end, 120, X) == best_line(df.iloc[:end + 1], end, 120, X), end


def test_scale_invariance():
    rng = np.random.default_rng(10)
    close = 100 * np.exp(np.cumsum(rng.normal(0, 0.03, 260)))
    a, b = best_line(_df(close), 259, 200, X), best_line(_df(close * 3), 259, 200, X)
    assert a["slope"] == pytest.approx(b["slope"]) and b["y1"] - a["y1"] == pytest.approx(np.log(3))
    assert line_key(a) == line_key(b)
