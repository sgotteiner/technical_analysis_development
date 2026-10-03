"""
The owner's search: walk back for the previous time price was at this level, stop at the first
whose move is the same size (2026-10-03). The things that must be true:

  - it STOPS at the match and does not read the rest of history
  - "30 here 30 then" - the comparison is with the current state, never with the era it happened in
  - no window: a very old point is reachable if nothing nearer matched
  - "or whatever you can find in that level" when nothing matches
"""
import numpy as np
import pytest
from business_logic_services.precedents import (SIMILAR_HI, SIMILAR_LO, picture_starts_at,
                                                precedent_at, similar_move)

# bars, the price each point reached, and the move that got there
BARS = np.array([100.0, 200.0, 300.0, 400.0, 500.0])
PRICES = np.array([80000.0, 50000.0, 80000.0, 60000.0, 80000.0])
MOVES = np.array([30.0, 20.0, 10.0, 15.0, 29.0])
NOW, CURRENT = 600.0, 30.0


def test_it_stops_at_the_first_match_walking_back():
    p = precedent_at(80000, CURRENT, BARS, PRICES, MOVES, 1.0, NOW)
    assert p["bar"] == 500.0, "the most recent one at the level already matches"
    assert p["matched"] and p["checked"] == 1, "it must not keep reading history after a match"


def test_it_keeps_walking_past_a_level_whose_move_was_the_wrong_size():
    moves = np.array([30.0, 20.0, 10.0, 15.0, 10.0])      # the newest at the level is now 10%
    p = precedent_at(80000, CURRENT, BARS, PRICES, moves, 1.0, NOW)
    assert p["bar"] == 100.0, "it walked back past the 10% one to the 30% one"
    assert p["matched"] and p["checked"] == 3


def test_nothing_similar_gives_whatever_is_at_that_level():
    """'or whatever you can find in that level.'"""
    moves = np.array([5.0, 20.0, 6.0, 15.0, 7.0])
    p = precedent_at(80000, CURRENT, BARS, PRICES, moves, 1.0, NOW)
    assert p["matched"] is False
    assert p["bar"] == 500.0, "the most recent one at the level, since none matched"


def test_a_level_price_has_never_been_at_has_no_precedent():
    assert precedent_at(123456, CURRENT, BARS, PRICES, MOVES, 1.0, NOW) is None


def test_there_is_no_window_so_a_far_older_point_is_still_reachable():
    """'you dont limit to less days' - if nothing nearer matched, the old one is the answer."""
    bars = np.array([10.0, 2000.0, 2500.0])
    prices = np.array([80000.0, 80000.0, 80000.0])
    moves = np.array([30.0, 8.0, 9.0])
    p = precedent_at(80000, CURRENT, bars, prices, moves, 1.0, 3000.0)
    assert p["bar"] == 10.0 and p["matched"], "age never disqualifies it"


def test_the_comparison_is_with_now_not_with_the_era():
    """'nothing for then. you dont compare with previous era. 30 here 30 then.'"""
    assert similar_move(30.0, 30.0)
    assert not similar_move(10.0, 30.0), "10% then is not the same as 30% now, whatever 2021 was like"
    assert similar_move(30.0 * SIMILAR_LO, 30.0) and similar_move(30.0 * SIMILAR_HI, 30.0)
    assert not similar_move(30.0 * (SIMILAR_LO - 0.05), 30.0)


def test_the_picture_reaches_back_to_the_precedent_and_no_further():
    assert picture_starts_at(80000, CURRENT, BARS, PRICES, MOVES, 1.0, NOW) == 500.0
    moves = np.array([30.0, 20.0, 10.0, 15.0, 10.0])
    assert picture_starts_at(80000, CURRENT, BARS, PRICES, moves, 1.0, NOW) == 100.0


def test_it_does_not_read_the_whole_history_when_it_does_not_have_to():
    """The point of stopping: the work is bounded by how far back the match is."""
    bars = np.arange(1.0, 2001.0)
    prices = np.full(2000, 80000.0)
    moves = np.full(2000, 30.0)
    p = precedent_at(80000, CURRENT, bars, prices, moves, 1.0, 2001.0)
    assert p["checked"] == 1, f"it read {p['checked']} points to find the one next door"
