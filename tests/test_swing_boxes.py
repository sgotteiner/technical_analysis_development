"""
Peaks and valleys as boxes (owner, 2026-10-03: "peak is from support to resistance to support and
valley is the opposite. i need to see what you do").
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.sr_turning_points import turning_points
from modules.shapes.swing_boxes import swing_boxes


def chart(prices):
    p = np.array(prices, dtype=float)
    idx = pd.date_range("2024-01-01", periods=len(p), freq="D", tz="UTC")
    return pd.DataFrame({"Open": p, "High": p, "Low": p, "Close": p}, index=idx)


def ramp(a, b, n):
    return list(np.linspace(a, b, n))[1:]


@pytest.fixture
def zigzag():
    # 100 -> 150 -> 110 -> 170 -> 120 -> 180: long enough to hold a CLOSED peak box (the 170)
    return chart([100] + ramp(100, 150, 15) + ramp(150, 110, 15) + ramp(110, 170, 15)
                 + ramp(170, 120, 15) + ramp(120, 180, 15))


def boxes(df, size=0.10):
    end = len(df) - 1
    return swing_boxes(turning_points(df, size), df["High"].to_numpy(), df["Low"].to_numpy(), end)


def test_a_peak_box_runs_from_the_support_before_to_the_support_after(zigzag):
    b = next(x for x in boxes(zigzag) if x["kind"] == "peak" and not x["open"])
    assert b["top"] == pytest.approx(170, abs=1), "the top is the peak itself"
    assert b["bottom"] == pytest.approx(110, abs=2), "the bottom is the lower support of the two"
    assert b["from_bar"] < b["bar"] < b["to_bar"], "it spans the whole journey, not just the high"


def test_a_valley_box_is_the_opposite(zigzag):
    b = next(x for x in boxes(zigzag) if x["kind"] == "valley" and not x["open"])
    assert b["bottom"] == pytest.approx(110, abs=1), "the bottom is the valley itself"
    assert b["top"] == pytest.approx(170, abs=2), "the top is the higher resistance of the two"
    assert b["from_bar"] < b["bar"] < b["to_bar"]


def test_the_box_carries_the_move_in_and_the_move_out(zigzag):
    b = next(x for x in boxes(zigzag) if x["kind"] == "peak" and not x["open"])
    assert b["up_pct"] == pytest.approx(54.5, abs=2), "110 -> 170 got it there"
    assert b["down_pct"] == pytest.approx(29.4, abs=2), "170 -> 120 took it away"


def test_the_last_one_is_still_forming_and_says_so(zigzag):
    last = boxes(zigzag)[-1]
    assert last["open"] is True, "its far side has not happened yet"
    assert last["to_bar"] == len(zigzag) - 1, "so it runs to now"
    assert not any(b["open"] for b in boxes(zigzag)[:-1]), "only the last one is open"


def test_it_never_uses_a_point_that_is_not_confirmed_yet(zigzag):
    """Boxes at an earlier 'now' must match what that day could have known."""
    end = 40
    high, low = zigzag["High"].to_numpy(), zigzag["Low"].to_numpy()
    tp = turning_points(zigzag, 0.10)
    early = swing_boxes(tp, high, low, end)
    assert all(b["to_bar"] <= end and b["from_bar"] <= end for b in early)
    full = swing_boxes(turning_points(zigzag.iloc[:end + 1], 0.10),
                       high[:end + 1], low[:end + 1], end)
    assert [b["bar"] for b in early] == [b["bar"] for b in full], "same answer with no later data"


def test_too_few_points_is_not_a_crash():
    assert swing_boxes(turning_points(chart([100] * 20), 0.10),
                       np.full(20, 100.0), np.full(20, 100.0), 19) == []
