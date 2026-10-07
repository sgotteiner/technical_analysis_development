"""
Touch zones (modules/shapes/touch_zones.py), against the picture he drew rather than a synthetic
case: a flat line at ~30,800 across 2023 with two boxes ON it, saved as the "just showing you"
sketch group `gmuuca0qu` on 2026-10-05.

  his zone 1   2023-04-09 -> 04-21   12 days   2.85% tall
  his zone 2   2023-06-19 -> 07-18   29 days   2.72% tall

and, not drawn by him, an October crossing that the same search finds - which is what the
touch/break rule has to tell apart.
"""
import numpy as np
import pytest
from modules.shapes.touch_zones import touch_zones

LINE = 30800.0
BAND = 1.4          # what his own box heights measure: 2.85% / 2.72% tall is +-1.4%


@pytest.fixture
def btc():
    from scripts.sr_playground import load_daily
    return load_daily()


def _in_2023(df, zones):
    return [z for z in zones if str(df.index[z["from_bar"]].date()).startswith("2023")]


def test_his_two_zones_are_found_and_the_crossing_is_not_a_touch(btc):
    high, low = btc["High"].to_numpy(), btc["Low"].to_numpy()
    end = max(i for i, t in enumerate(btc.index) if str(t.date()) <= "2024-12-06")
    zones = _in_2023(btc, touch_zones(LINE, BAND, high, low, end))
    touches = [z for z in zones if z["kind"] == "touch"]
    assert len(touches) == 2, [str(btc.index[z["from_bar"]].date()) for z in zones]

    first, second = touches
    assert str(btc.index[first["from_bar"]].date()) == "2023-04-11"      # he drew 04-09
    assert str(btc.index[first["to_bar"]].date()) == "2023-04-19"        # he drew 04-21
    assert str(btc.index[second["from_bar"]].date()) == "2023-06-21"     # he drew 06-19
    assert str(btc.index[second["to_bar"]].date()) == "2023-07-20"       # he drew 07-18
    # his boxes are 2.85% and 2.72% tall; the band reproduces that, and the candles stick out
    assert first["height_pct"] == pytest.approx(2.84, abs=0.05)
    assert first["reach_top"] > first["top"] or first["reach_bottom"] < first["bottom"]

    crossing = [z for z in zones if z["kind"] == "break"]
    assert len(crossing) == 1 and str(btc.index[crossing[0]["from_bar"]].date()) == "2023-10-21"
    assert (crossing[0]["came_from"], crossing[0]["left_to"]) == ("below", "above")


def test_a_touch_arrives_and_leaves_on_the_same_side():
    # down to the line, back up: a touch from above
    high = np.array([110.0, 104, 101, 100.6, 104, 112], dtype=float)
    low = np.array([106.0, 100, 99.5, 99.4, 100, 108], dtype=float)
    z = touch_zones(100.0, 1.0, high, low, len(high) - 1, min_bars=2)
    assert len(z) == 1 and z[0]["kind"] == "touch"
    assert (z[0]["came_from"], z[0]["left_to"]) == ("above", "above")


def test_a_crossing_is_a_break_not_a_touch():
    high = np.array([96.0, 99, 100.5, 101, 106, 112], dtype=float)
    low = np.array([92.0, 95, 99.2, 100, 104, 108], dtype=float)
    z = touch_zones(100.0, 1.0, high, low, len(high) - 1, min_bars=2)
    assert len(z) == 1 and z[0]["kind"] == "break"
    assert (z[0]["came_from"], z[0]["left_to"]) == ("below", "above")


def test_one_bar_through_the_level_is_not_a_zone():
    high = np.array([96.0, 100.5, 112, 118], dtype=float)
    low = np.array([92.0, 99.5, 108, 114], dtype=float)
    assert touch_zones(100.0, 1.0, high, low, 3, min_bars=2) == []


def test_price_leaving_and_coming_back_makes_two_zones():
    high = np.array([101.0, 100.8, 94, 90, 92, 100.7, 101.2, 108], dtype=float)
    low = np.array([99.5, 99.4, 90, 86, 88, 99.6, 99.8, 104], dtype=float)
    z = touch_zones(100.0, 1.0, high, low, 7, min_bars=2, min_gap=2)
    assert len(z) == 2
    assert (z[0]["from_bar"], z[0]["to_bar"]) == (0, 1)
    assert (z[1]["from_bar"], z[1]["to_bar"]) == (5, 6)
