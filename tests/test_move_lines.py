"""
Lines ranked by the move that ran into them, and the trade they describe.

The test that matters is his own chart: the rule must put the line he called important
("same move and same resistance") above the one he called "weak short term", and must stop
drawing a line from touches he said he would never draw from.
"""
import numpy as np
import pytest
from business_logic_services.move_lines import ladder_by_move, lines_by_move
from modules.shapes.sr_turning_points import turning_points, PEAK
from modules.shapes.swing_moves import leg_moves, running_move
from scripts.sr_playground import load_daily

SIZE = 0.09          # the size he picked: "9 is better"
BAND = SIZE * 100 / 2    # "band width from the swing size, about half a swing" (his rule)
AGE_SCALE = 700.0        # the one knob, to be searched against his verdicts


@pytest.fixture(scope="module")
def chart():
    df = load_daily()
    last = len(df) - 1
    high, low = df["High"].to_numpy(), df["Low"].to_numpy()
    tp = turning_points(df, SIZE)
    known = (tp["conf"] <= last) & (tp["idx"] <= last)
    all_moves = leg_moves(tp, high, low)
    x = tp["idx"][known].astype(float)
    y = np.where(tp["kind"][known] == PEAK, np.log(high[tp["idx"][known]]),
                 np.log(low[tp["idx"][known]]))
    now_move, _, _ = running_move(tp, high, low, last)
    return {"df": df, "last": last, "x": x, "y": y, "kinds": tp["kind"][known],
            "moves": all_moves[known], "now_move": now_move,
            "price_now": float(df["Close"].iloc[last]),
            "price_before": float(df["Close"].iloc[last - 10])}


def run(chart, **kw):
    args = dict(band_pct=BAND, price_now=chart["price_now"], price_before=chart["price_before"],
                end=chart["last"], current_move=chart["now_move"], age_scale=AGE_SCALE, min_touches=2)
    args.update(kw)
    return lines_by_move(chart["x"], chart["y"], chart["kinds"], chart["moves"], **args)


def near(lines, price, tol=0.02):
    return next((l for l in lines if abs(l["price"] / price - 1) <= tol), None)


def test_the_line_he_called_important_ranks_first(chart):
    """'important line because its the same move and same resistance.' Price is standing on it,
    so it is the first rung of the ladder, and its move matches the move running now."""
    lines = run(chart)
    assert lines, "the rule returns something"
    top = lines[0]
    assert abs(top["price"] / 82000 - 1) < 0.04, f"expected the ~82k resistance, got {top['price']:,.0f}"
    assert top["vs_now"] >= 0.75 and top["term"] == "this move"


def test_the_67_line_comes_out_as_the_smaller_move_he_described(chart):
    """He kept it but called it 'a weak short term support'; its move was 'about 10%' vs ~28%."""
    lines = run(chart)
    line = near(lines, 66956, 0.05)
    assert line is not None, "it is still found - he said the line is good"
    assert line["vs_now"] < 0.75, f"but not this move: {line['vs_now']:.2f}x"
    assert line["move"] < chart["now_move"], "the moves it turned were smaller than the one running"


def test_the_important_line_outranks_the_short_term_one(chart):
    lines = run(chart)
    order = [round(l["price"]) for l in lines]
    big, small = near(lines, 82000, 0.04), near(lines, 66956, 0.05)
    assert big is not None and small is not None
    assert order.index(round(big["price"])) < order.index(round(small["price"])), order


def test_a_line_is_not_drawn_from_touches_too_old_for_their_move(chart):
    """'i woudnt draw it from that long before' - the 2021 touch of the 67 line."""
    line = near(run(chart), 66956, 0.05)
    assert line["dropped"] > 0, "some touches were too small for their age"
    oldest = chart["last"] - line["first"]
    assert oldest < 1500, f"it still starts {oldest:.0f} days back"


def test_a_bigger_age_scale_keeps_more_history(chart):
    """The one knob, and it moves the way it should - it is meant to be searched, not chosen.

    Tight enough and a line disappears altogether, which is the extreme of keeping less history.
    """
    kept = []
    for scale in (300.0, 700.0, 2000.0):
        line = near(run(chart, age_scale=scale), 66956, 0.05)
        kept.append((0, chart["last"]) if line is None else (line["touches"], chart["last"] - line["first"]))
    touches = [k[0] for k in kept]
    assert touches == sorted(touches), f"more scale must never keep fewer touches: {touches}"
    assert touches[0] < touches[-1], "the knob has to actually do something"
    reach = [k[1] for k in kept if k[0]]
    assert reach == sorted(reach), f"more scale must never reach less far back: {reach}"


def test_two_lines_never_sit_closer_than_the_band(chart):
    lines = run(chart)
    prices = sorted(l["price"] for l in lines)
    for a, b in zip(prices, prices[1:]):
        assert (b / a - 1) * 100 >= BAND - 1e-6, f"{a:,.0f} and {b:,.0f} are too close"


def test_the_ladder_reads_the_trade_off_the_lines(chart):
    """Entry, the stop below it, and the rungs above in order - with R, not just prices."""
    lad = ladder_by_move(run(chart), chart["price_now"])
    assert lad["entry"] and lad["stop"] and lad["stop"] < lad["entry"]
    assert lad["risk_pct"] > 0
    assert lad["targets"], "there is something above to aim at"
    assert all(t["price"] > lad["entry"] for t in lad["targets"])
    assert [t["price"] for t in lad["targets"]] == sorted(t["price"] for t in lad["targets"])
    assert lad["targets"][0]["r"] > 0


def test_nothing_in_nothing_out():
    empty = np.array([])
    assert lines_by_move(empty, empty, empty, empty, BAND, 100, 99, 10, current_move=20) == []
    assert lines_by_move(np.array([1.0, 2.0]), np.log([100.0, 110.0]), np.array([1, -1]),
                         np.array([5.0, 5.0]), BAND, 100, 99, 10, current_move=0) == []
