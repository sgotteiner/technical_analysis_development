"""
Tests for price zones (modules/shapes/price_zones.py), the owner's rules (2026-09-24):
  - a zone is a price BAND whose width comes from the swing size in percent (about half a swing),
    so it is scale-free: "you can count on the same metric of percentage to see similar moves";
  - its strength is VISITS, not touches: price must leave the zone and come back for a new visit
    ("measure the moves time"). Three wiggles in one week are one visit;
  - the line is drawn at the strongest price inside the band;
  - the current price is always a candidate zone, whether or not a swing point sits there;
  - a zone price is standing on is labelled by the direction it arrived from: came up = resistance,
    came down = support.
"""
import numpy as np
import pytest
from modules.shapes.price_zones import price_zones, label_for

PEAK, VALLEY = 1, -1


def _pts(pairs):
    return (np.array([p[0] for p in pairs], dtype=float),
            np.log(np.array([p[1] for p in pairs], dtype=float)),
            np.array([p[2] for p in pairs], dtype=int))


def test_near_prices_become_one_zone_at_the_strongest_price():
    # 57.8 / 59.1 / 58.0 are one support zone; 70 is another
    x, y, k = _pts([(0, 57800, VALLEY), (20, 70000, PEAK), (40, 59131, VALLEY), (60, 70000, PEAK),
                    (80, 58000, VALLEY), (100, 69800, PEAK)])
    zones = price_zones(x, y, k, band_pct=4.5, now_price=65000, now_bar=100)
    prices = sorted(round(z["price"]) for z in zones)
    assert len(zones) == 2, [round(z["price"]) for z in zones]
    assert 57000 <= prices[0] <= 59500 and 69000 <= prices[1] <= 70500


def test_visits_need_price_to_leave_and_come_back():
    # three touches of the same zone in a row, without leaving it, are one visit
    x, y, k = _pts([(0, 60000, VALLEY), (2, 60500, PEAK), (4, 60200, VALLEY),
                    (30, 80000, PEAK), (60, 60300, VALLEY)])
    zone = price_zones(x, y, k, band_pct=4.5, now_price=70000, now_bar=60)[0]
    assert zone["touches"] == 4 and zone["visits"] == 2
    assert zone["last_visit"] == 60 and zone["first_visit"] == 0


def test_zones_are_ranked_by_visits_then_recency():
    x, y, k = _pts([(0, 50000, VALLEY), (10, 70000, PEAK), (20, 50100, VALLEY), (30, 70200, PEAK),
                    (40, 49900, VALLEY), (50, 90000, PEAK)])
    zones = price_zones(x, y, k, band_pct=4.0, now_price=80000, now_bar=50)
    assert [z["visits"] for z in zones] == sorted([z["visits"] for z in zones], reverse=True)
    assert round(zones[0]["price"], -3) == 50000


def test_the_current_price_is_always_a_zone_even_without_a_recent_point():
    """80.3k: history visited it, the recent swing points did not (owner's missing line)."""
    x, y, k = _pts([(0, 80600, PEAK), (30, 60000, VALLEY), (60, 81500, PEAK), (90, 64000, VALLEY)])
    zones = price_zones(x, y, k, band_pct=4.5, now_price=81076, now_bar=120)
    here = [z for z in zones if z["at_price_now"]]
    assert here and 79000 <= here[0]["price"] <= 82000
    assert here[0]["visits"] == 2


def test_a_zone_far_from_price_is_not_marked_as_current():
    x, y, k = _pts([(0, 50000, VALLEY), (20, 70000, PEAK), (40, 50200, VALLEY)])
    zones = price_zones(x, y, k, band_pct=4.0, now_price=90000, now_bar=60)
    assert not any(z["at_price_now"] for z in zones)


@pytest.mark.parametrize("came_from, expected", [(70000, "support"), (60000, "resistance")])
def test_a_zone_price_stands_on_is_labelled_by_where_price_came_from(came_from, expected):
    assert label_for(zone_price=65000, price_now=65100, price_before=came_from) == expected


def test_a_zone_below_price_is_support_and_above_is_resistance():
    assert label_for(zone_price=50000, price_now=65000, price_before=64000) == "support"
    assert label_for(zone_price=80000, price_now=65000, price_before=64000) == "resistance"


def test_the_ladder_answers_from_the_current_price():
    """Owner, 2026-09-24: "what is my current support and resistance ... and whats the next ones"."""
    from modules.shapes.price_zones import ladder
    x, y, k = _pts([(0, 50000, VALLEY), (10, 65000, PEAK), (20, 50200, VALLEY), (30, 80000, PEAK),
                    (40, 65200, VALLEY), (50, 80500, PEAK), (60, 100000, PEAK), (70, 65100, VALLEY),
                    (80, 99500, PEAK), (90, 65050, VALLEY)])
    zones = price_zones(x, y, k, band_pct=4.0, now_price=65100, now_bar=90)
    lad = ladder(zones, price_now=65100, price_before=60000, n_each=2, min_visits=2)
    assert lad["on"] and round(lad["on"]["price"], -3) == 65000
    assert lad["on"]["label"] == "resistance"                      # price came up to it
    assert [round(z["price"], -3) for z in lad["above"]] == [80000, 100000]
    assert [round(z["price"], -3) for z in lad["below"]] == [50000]
    assert all(z["label"] == "resistance" for z in lad["above"])
    assert all(z["label"] == "support" for z in lad["below"])


def test_the_ladder_says_when_price_is_between_levels():
    from modules.shapes.price_zones import ladder
    x, y, k = _pts([(0, 50000, VALLEY), (10, 80000, PEAK), (20, 50200, VALLEY), (30, 80500, PEAK)])
    zones = price_zones(x, y, k, band_pct=4.0, now_price=65000, now_bar=40)
    lad = ladder(zones, price_now=65000, price_before=60000, n_each=2, min_visits=2)
    assert lad["on"] is None
    assert round(lad["above"][0]["price"], -3) == 80000 and round(lad["below"][0]["price"], -3) == 50000


def test_weak_zones_are_left_out_of_the_ladder():
    from modules.shapes.price_zones import ladder
    x, y, k = _pts([(0, 50000, VALLEY), (10, 70000, PEAK), (20, 50100, VALLEY), (30, 90000, PEAK)])
    zones = price_zones(x, y, k, band_pct=4.0, now_price=60000, now_bar=40)
    lad = ladder(zones, price_now=60000, price_before=55000, n_each=3, min_visits=2)
    assert [round(z["price"], -3) for z in lad["above"]] == []      # 70k and 90k have one visit each
    assert [round(z["price"], -3) for z in lad["below"]] == [50000]


def test_empty_input_still_gives_the_current_price_zone_only_if_it_has_visits():
    empty = np.array([])
    assert price_zones(empty, empty, empty.astype(int), 4.0, now_price=100, now_bar=10) == []
