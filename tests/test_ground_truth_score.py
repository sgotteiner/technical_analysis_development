"""
Tests for scoring the found lines against the owner's drawings
(business_logic_services/ground_truth_score.py). The owner, 2026-09-24: "did you compare to my
ground truth setup? remember the goal is to find setups like me?"

For the day a drawing was made: a horizontal drawing is FOUND when a zone sits within `tol` of it
at that day's price; a diagonal is FOUND when a trend line is within `tol` at "now" and its slope
is close. Anything found that he did not draw is EXTRA.
"""
import numpy as np
import pytest
from business_logic_services.ground_truth_score import score_against_drawings


T0 = 1_700_000_000
T1 = T0 + 350 * 86400          # a line drawn across ~a year, like the owner's


def _drawing(label, p0, p1, t0=T0, t1=T1, drawn_at=T1):
    return {"kind": "line", "label": label, "drawn_at": drawn_at,
            "points": [{"time": t0, "price": p0}, {"time": t1, "price": p1}]}


FOUND = {"zones": [{"price": 80000, "visits": 3}, {"price": 60000, "visits": 2}],
         "trends": [{"at_now": 65000, "slope_pct_day": -0.20}]}


def test_a_drawn_level_within_tolerance_counts_as_found():
    drawings = [_drawing("current resistance", 79500, 80200)]
    got = score_against_drawings(drawings, FOUND, price_now=81000, tol_pct=3)
    assert got["found"] == 1 and got["missed"] == 0
    assert got["lines"][0]["found"] and got["lines"][0]["by"] == pytest.approx(80000)


def test_a_drawn_level_nobody_found_is_missed():
    drawings = [_drawing("next resistance", 106000, 106200)]
    got = score_against_drawings(drawings, FOUND, price_now=81000, tol_pct=3)
    assert got["found"] == 0 and got["missed"] == 1 and got["lines"][0]["by"] is None


def test_a_diagonal_is_matched_on_price_and_slope():
    diag = _drawing("previous resistance", 135000, 66000)          # falls to 66k at the end
    got = score_against_drawings([diag], FOUND, price_now=81000, tol_pct=3)
    assert got["found"] == 1 and got["lines"][0]["kind"] == "trend"


def test_a_diagonal_with_the_wrong_slope_is_not_a_match():
    diag = _drawing("rising line", 40000, 65000)                   # rises to the same price
    got = score_against_drawings([diag], FOUND, price_now=81000, tol_pct=3)
    assert got["found"] == 0


def test_extras_are_counted_and_named():
    drawings = [_drawing("current resistance", 79500, 80200)]
    got = score_against_drawings(drawings, FOUND, price_now=81000, tol_pct=3)
    assert [round(e["price"]) for e in got["extra"]] == [60000, 65000]     # the unused trend counts too


def test_boxes_and_other_drawings_are_ignored():
    box = {"kind": "box", "label": "bull flag", "drawn_at": 1_700_000_000,
           "points": [{"time": 1, "price": 10}, {"time": 2, "price": 20}]}
    got = score_against_drawings([box, _drawing("support", 60000, 60100)], FOUND, price_now=81000, tol_pct=3)
    assert got["total"] == 1 and got["found"] == 1


def test_nothing_drawn_gives_an_empty_score():
    got = score_against_drawings([], FOUND, price_now=81000, tol_pct=3)
    assert got["total"] == 0 and got["found"] == 0 and len(got["extra"]) == 3
