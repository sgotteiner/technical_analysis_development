"""
Lines from the zigzag, kept (business_logic_services/zigzag_lines.py), at his 2025-04 example: the
falling trend line through the January peaks stays until a close breaks it, and nothing in a day's
lines comes from a later day.
"""
import pandas as pd
from business_logic_services.zigzag_lines import _at, at_day
from scripts.sr_playground import load_daily


def _ix(df, day):
    return int(df.index.get_indexer([pd.Timestamp(day, tz="UTC")])[0])


def test_the_trend_line_lives_as_long_as_the_trend():
    """2025-04: the down trend from the 109,588 top, its line through his dots (01-20, 01-30); a close
    above it is its breakout, not its end - "a trend is not over with a close above" (2026-10-09)."""
    df, cache = load_daily(), {}
    later, after = (at_day(df, _ix(df, d), 0.07, cache)["trends"][0] for d in ("2025-04-14", "2025-04-22"))
    assert later["points"] == after["points"]                               # the same line after its breakout
    assert abs(later["prices"][0] / 109_588 - 1) < 0.01 and abs(later["prices"][1] / 106_457 - 1) < 0.01
    assert abs(_at(later, _ix(df, "2025-04-14")) / 84_788 - 1) < 0.03       # his line that day
    assert later["broken"] is None and after["broken"] is not None         # broken on the way up, still there


def test_his_trend_lines_start_where_the_trend_began():
    """2022-03-04: the down trend from the 2021-11-10 top (69,000). 2026-02-13: his line through
    126,200 and 97,924, at 92,973 that day."""
    df, cache = load_daily(), {}
    t22 = at_day(df, _ix(df, "2022-03-04"), 0.07, cache)["trends"][0]
    assert t22["down"] and abs(t22["prices"][0] / 69_000 - 1) < 0.01
    e = _ix(df, "2026-02-13")
    t26 = at_day(df, e, 0.07, cache)["trends"][0]
    assert abs(_at(t26, e) / 92_973 - 1) < 0.03


def test_the_lines_change_only_when_the_zigzag_makes_a_point():
    """"zigzag didnt make a new point you dont create a new sr line" (owner, 2026-10-08)."""
    df, cache = load_daily(), {}
    prev = None
    for d in range(_ix(df, "2025-01-01"), _ix(df, "2025-07-01")):
        g = at_day(df, d, 0.07, cache)
        now = (tuple(round(l["price"]) for l in g["levels"]), [p[:3] for p in g["points"]])
        if prev is not None and now[0] != prev[0]:
            assert now[1] != prev[1], df.index[d].date()       # a line moved with no new zigzag point
        prev = now


def test_a_new_point_on_an_old_line_touches_it():
    """2025-04-07: the new valley at 74,508 lands on the line at ~73.8k (the March 2024 high)."""
    df = load_daily()
    support = [l for l in at_day(df, _ix(df, "2025-04-14"), 0.07, {})["levels"] if l["price"] < 80_000][0]
    assert abs(support["price"] / 73_800 - 1) < 0.015 and len(support["touches"]) >= 3


def test_one_zigzag_point_is_not_a_line():
    """"why is this a resistance ... it touches one zigzag point" (2022-07-08, the 20,918 of 07-01)."""
    df = load_daily()
    lv = at_day(df, _ix(df, "2022-07-08"), 0.07, {})["levels"]
    assert lv and all(len(l["touches"]) >= 2 for l in lv)
    assert not any(abs(l["price"] / 20_918 - 1) < 0.01 for l in lv)


def test_a_day_uses_nothing_after_it():
    df = load_daily()
    cut = _ix(df, "2025-04-17")
    full, short = at_day(df, cut, 0.07, {}), at_day(df.iloc[:cut + 1], cut, 0.07, {})
    assert full["levels"] == short["levels"]
    assert [(l["points"], l["broken"]) for l in full["trends"]] == [(l["points"], l["broken"]) for l in short["trends"]]
