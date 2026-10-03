"""
The owner's measure: a touch is worth the MOVE THAT RAN INTO IT, and what matters now is how that
compares with the move running now (2026-10-03, on his 80k sketch).

The anchor case is his own: the May 2026 peak and the leg running now are the same move off the
same valley level into the same resistance - that is why he calls that line the important one.
"""
import numpy as np
import pandas as pd
import pytest
from modules.shapes.swing_moves import leg_moves, required_move, running_move
from modules.shapes.sr_turning_points import turning_points
from scripts.sr_playground import load_daily


def chart(prices):
    idx = pd.date_range("2024-01-01", periods=len(prices), freq="D", tz="UTC")
    p = np.array(prices, dtype=float)
    return pd.DataFrame({"Open": p, "High": p, "Low": p, "Close": p}, index=idx)


def ramp(a, b, n):
    return list(np.linspace(a, b, n))[1:]


def test_a_leg_is_measured_from_the_turn_before_it():
    df = chart([100] + ramp(100, 150, 20) + ramp(150, 120, 20) + ramp(120, 180, 25))
    tp = turning_points(df, 0.10)
    moves = leg_moves(tp, df["High"].to_numpy(), df["Low"].to_numpy())
    assert len(moves) == len(tp["idx"])
    assert moves[0] == 0, "the first point has nothing before it"
    assert moves[1] == pytest.approx(20.0, abs=0.5), "150 -> 120 is a 20% leg"


def test_the_running_move_counts_the_part_that_has_not_finished():
    """He reads the picture as a move still deciding, so the open leg is the one that matters."""
    df = chart([100] + ramp(100, 150, 20) + ramp(150, 120, 20) + ramp(120, 168, 25))
    tp = turning_points(df, 0.10)
    end = len(df) - 1
    pct, start, direction = running_move(tp, df["High"].to_numpy(), df["Low"].to_numpy(), end)
    assert direction == 1, "price is rallying off a valley"
    assert pct == pytest.approx(40.0, abs=1.0), "120 -> 168 is 40%, open or not"
    assert df.index[start].strftime("%m-%d") != df.index[end].strftime("%m-%d")


def test_the_running_move_is_bigger_than_the_last_completed_leg():
    df = chart([100] + ramp(100, 150, 20) + ramp(150, 120, 20) + ramp(120, 168, 25))
    tp = turning_points(df, 0.10)
    completed = leg_moves(tp, df["High"].to_numpy(), df["Low"].to_numpy())[-1]
    running, _, _ = running_move(tp, df["High"].to_numpy(), df["Low"].to_numpy(), len(df) - 1)
    assert running > completed, "the open leg has run further than the last finished one"


def test_an_older_touch_has_to_have_moved_more_to_still_count():
    req = required_move(np.array([30, 365, 1780]), current_move=28.0, age_scale=365)
    assert req[0] < req[1] < req[2], "the earlier it is, the bigger the move it has to relate to"
    assert req[1] == pytest.approx(28.0), "at the scale age, it must match the move running now"
    assert req[2] > 100, "a touch from five years back needs a huge move"


def test_his_own_case_the_may_peak_and_now_are_the_same_move():
    """The anchor: 'previous 80k resistance after about 25% move like the current move'."""
    df = load_daily()
    last = len(df) - 1
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    tp = turning_points(df, 0.09)                     # the size he picked: "9 is better"
    moves = leg_moves(tp, high, low)
    days = df.index.strftime("%Y-%m-%d")
    may = [j for j, i in enumerate(tp["idx"]) if days[i] == "2026-05-06"]
    assert may, "the May 2026 peak is a 9% turning point"
    may_move = moves[may[0]]
    now_move, start, direction = running_move(tp, high, low, last)
    assert may_move == pytest.approx(27.5, abs=1.0), f"his 'about 25%' = {may_move:.1f}%"
    assert now_move == pytest.approx(28.3, abs=1.0), f"the move running now = {now_move:.1f}%"
    assert abs(may_move - now_move) < 3, "the same move, which is his whole point"
    assert direction == 1 and days[start] == "2026-08-19", "off the valley that turned the downtrend"


def test_no_turning_points_is_not_a_crash():
    df = chart([100] * 30)
    tp = turning_points(df, 0.10)
    assert list(leg_moves(tp, df["High"].to_numpy(), df["Low"].to_numpy())) == []
    assert running_move(tp, df["High"].to_numpy(), df["Low"].to_numpy(), 29) == (0.0, 29, 0)
