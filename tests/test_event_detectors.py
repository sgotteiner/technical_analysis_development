"""
The event detectors (modules/events/detectors.py) on made-up closes around one line at 100 with a
zone of 98-102 - each case one where the answer is plain.
"""
import numpy as np
from modules.events.detectors import breakout, bounce, fakeout, retest, sweep

ZONE = lambda bar: (98.0, 102.0)


def bars(closes, highs=None, lows=None):
    c = np.array(closes, dtype=float)
    h = np.array(highs, dtype=float) if highs else c + 0.5
    l = np.array(lows, dtype=float) if lows else c - 0.5
    return c, h, l


def test_breakout_is_decided_on_the_first_close_beyond():
    c, h, l = bars([95, 96, 99, 103, 104])
    assert breakout(c, h, l, ZONE, 3)["direction"] == "up"
    assert breakout(c, h, l, ZONE, 4) is None                 # already beyond the day before


def test_breakout_with_two_closes_waits_for_the_second():
    c, h, l = bars([95, 99, 103, 104])
    assert breakout(c, h, l, ZONE, 2, closes=2) is None
    assert breakout(c, h, l, ZONE, 3, closes=2)["from_bar"] == 1   # it entered the zone on bar 1


def test_a_line_left_on_its_own_side_is_no_breakout():
    c, h, l = bars([104, 101, 103])                           # from above, into the zone, out above
    assert breakout(c, h, l, ZONE, 2) is None
    assert bounce(c, h, l, ZONE, 2)["direction"] == "up"


def test_fakeout_closes_beyond_then_back():
    c, h, l = bars([95, 103, 97])
    ev = fakeout(c, h, l, ZONE, 2)
    assert ev["direction"] == "down" and ev["from_bar"] == 1


def test_sweep_is_one_wick_through():
    c, h, l = bars([97, 99], highs=[97.5, 104], lows=[96.5, 98.5])
    assert sweep(c, h, l, ZONE, 1)["direction"] == "down"


def test_retest_is_the_first_return_that_holds():
    c, h, l = bars([95, 103, 106, 101], lows=[94.5, 102.5, 105.5, 101.5])
    ev = retest(c, h, l, ZONE, 3)
    assert ev["direction"] == "up" and ev["breakout_bar"] == 1


def test_bounce_off_support():
    c, h, l = bars([110, 105, 101, 104], lows=[109, 104, 99, 103])
    assert bounce(c, h, l, ZONE, 3)["direction"] == "up"
