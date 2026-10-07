"""
The trend at his own dates, read at the scale of the move running now
(business_logic_services/trend_structure.py), and the name of the level price is on.

Each expectation is his reading at that date, from his drawings or his words - not a number the
code happened to produce.
"""
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from business_logic_services.trend_state import at_bar
from business_logic_services.trend_structure import read_structure
from modules.shapes.sr_turning_points import turning_points
from modules.shapes.swing_moves import running_move
from scripts.sr_playground import create_app, load_daily

SIZE = 0.07                  # the page's size
HIS_ZONE_PCT = 2.85          # his own drawn touch zone (2023 picture): how far is "on his line"

# date -> (his direction, his trend line's price that day, from his drawn strokes)
HIS = {"2024-08-02": ("horizontal", None),         # sketch: "just a sideways range. no trend here"
       "2025-07-04": ("horizontal", None),         # 2026-10-06: "were in a 10% ranging pipe ..."
       # his note reads "long up trend" AND "current peaks are not getting higher but stay the same
       # hight"; price is inside that range, so by his 2026-10-06 rule the up trend is "the
       # previous trend if anything". Horizontal is that rule applied - not yet confirmed by him.
       "2025-10-03": ("horizontal", None),
       "2026-02-13": ("down", 92_973),             # sketch: lower peaks, -0.21%/day
       "2026-05-15": ("down", None),               # 2026-10-06: "the trend is a downtrend clearly"
       "2026-09-04": ("down", 65_733)}             # drawn "previous resistance", -0.20%/day


@pytest.fixture(scope="module")
def df():
    return load_daily()


def _trend(df, date):
    end = int(df.index.get_indexer([pd.Timestamp(date, tz="UTC")])[0])
    tp = turning_points(df, SIZE)
    move, _, _ = running_move(tp, df["High"].to_numpy(), df["Low"].to_numpy(), end,
                              float(df["Close"].iloc[end]), df["Close"].to_numpy())
    return end, read_structure(df, end, move, SIZE)[0]     # what the page itself uses


@pytest.mark.parametrize("date", list(HIS))
def test_the_direction_is_his(df, date):
    _, t = _trend(df, date)
    assert t is not None and t["direction"] == HIS[date][0], (date, t and t["direction"])


@pytest.mark.parametrize("date", [d for d, (_, line) in HIS.items() if line])
def test_the_line_sits_on_his_line(df, date):
    """Over the highs from where the down trend began - not a line fitted through price."""
    end, t = _trend(df, date)
    off = (at_bar(t, end) / HIS[date][1] - 1) * 100
    assert abs(off) <= HIS_ZONE_PCT, f"{date}: {at_bar(t, end):,.0f} is {off:+.1f}% from his line"


PAGE = {"mode": "owner", "tol_pct": 1.5, "min_touches": 3, "top": 6, "anchor_days": 120,
        "max_history": 2, "merge_pct": 0, "targets_each_way": 2, "min_visits": 2}


def _story(df, tmp_path, date):
    """What the page shows at `date`, through the real request."""
    client = TestClient(create_app(df, tmp_path / "gt.json"))
    end = int(df.index.get_indexer([pd.Timestamp(date, tz="UTC")])[0])
    got = client.post("/api/points", json={"end": end, "sizes": [SIZE], "lines": PAGE}).json()
    return got["sizes"][0]["story"]["lines"]


def test_the_page_draws_his_trend_line_not_one_through_price(df, tmp_path):
    """2026-02-13: the page used to draw the trend at 68,791 - on price - because a fitted line
    nearer price replaced the structure. His line is over the lower peaks, at 92,973."""
    trend = next(l for l in _story(df, tmp_path, "2026-02-13") if l["role"] == "the trend")
    assert abs(trend["price"] / 92_973 - 1) * 100 <= HIS_ZONE_PCT, f"{trend['price']:,.0f}"


@pytest.mark.parametrize("date", ["2025-10-03", "2026-05-15"])
def test_the_level_price_came_up_to_is_resistance(df, tmp_path, date):
    """2025-10-03: "the price is at the resistance" (up trend). 2026-05-15: "price is on a peak in
    this downtrend" - the 10-day rule called it support there."""
    roles = [l["role"] for l in _story(df, tmp_path, date)]
    assert "the level price is on (resistance)" in roles, roles


def test_a_level_price_only_passes_through_is_not_the_one_it_is_on(df, tmp_path):
    """2024-10-25: the move turned at 69,520 and price fell back through 66,867 - "i dont think its
    on a line i would remove it". He kept the level above and the level below."""
    lines = {l["role"]: l["price"] for l in _story(df, tmp_path, "2024-10-25")}
    assert not any(r.startswith("the level price is on") for r in lines), lines
    assert abs(lines["resistance above"] / 69_538 - 1) * 100 <= HIS_ZONE_PCT, lines
    assert abs(lines["support below"] / 64_478 - 1) * 100 <= HIS_ZONE_PCT, lines


def test_inside_a_range_the_lines_are_its_walls(df, tmp_path):
    """2024-08-02, his sketch: "just a sideways range ... the pipe is about 25%", top drawn at
    68,677-73,777 and floor at 53,927-59,968. The page drew three lines 4-5% apart inside it."""
    lines = {l["role"]: l["price"] for l in _story(df, tmp_path, "2024-08-02")}
    assert 68_677 <= lines["resistance above"] <= 73_777, lines
    assert 53_927 <= lines["support below"] <= 59_968, lines


@pytest.mark.parametrize("date", ["2024-08-02", "2025-07-04"])
def test_sideways_draws_no_trend_line(df, tmp_path, date):
    """"its sideways. draw only whats there" (2026-10-06): the range's walls, no 1% 'trend'."""
    roles = [l["role"] for l in _story(df, tmp_path, date)]
    assert "the trend" not in roles, roles
    assert "resistance above" in roles and "support below" in roles, roles


@pytest.mark.parametrize("date", list(HIS) + ["2024-10-25", "2025-04-25", "2026-04-10"])
def test_never_more_than_four_lines(df, tmp_path, date):
    """Support and resistance, the trend if there is one, and the level price is on plus the next
    one past it: "so maximum 4 lines" (2026-10-06)."""
    assert len(_story(df, tmp_path, date)) <= 4


def test_an_up_trend_under_a_flat_top_has_the_top_as_resistance(df, tmp_path):
    """2023-08-11, his drawing: rising valleys under peaks at one height, 31,000 (04-14) and
    31,804 (07-13); he draws the resistance flat at ~31,450. The 7% clusters gave 30,036."""
    lines = {l["role"]: l["price"] for l in _story(df, tmp_path, "2023-08-11")}
    assert abs(lines["resistance above"] / 31_450 - 1) * 100 <= HIS_ZONE_PCT, lines


def test_a_line_steeper_than_a_swing_is_one_leg_not_the_trend(df):
    """2023-04-21: the March 2023 huge candles drew the trend at +1.81%/day through two pullbacks
    of one rally, 52% over price ("i think the huge candles confused you"). A trend line may not
    move more in one swing than "the same level" allows; his own line (drawn 2023-08-11) runs from
    the December low through the March low and is at ~21,700 here."""
    end, t = _trend(df, "2023-04-21")
    assert abs(at_bar(t, end) / 21_700 - 1) * 100 <= HIS_ZONE_PCT, f"{at_bar(t, end):,.0f}"


def test_in_an_up_trend_the_resistance_is_the_latest_peak(df, tmp_path):
    """2023-04-21, pulling back from the 31,000 peak in an up trend: "should have been at the peak
    of about 31400" - the page had a 7% cluster at 29,242 in between."""
    lines = {l["role"]: l["price"] for l in _story(df, tmp_path, "2023-04-21")}
    assert abs(lines["resistance above"] / 31_400 - 1) * 100 <= HIS_ZONE_PCT, lines


def test_a_trend_line_out_of_the_moves_reach_is_drawn_but_marked_far(df, tmp_path):
    """2023-04-21: the up trend line is 21.1% under price in a 12.1% move - "not related to the
    trade". Hiding it left two flat lines and no trend, a pipe without its trend (2023-03-24: "dont
    you see there are only lines and no trend"). So it is drawn, marked far; your 2026-02-13 down
    trend, 31.8% over price in a 29.7% move ("the trend is also kind of resistance"), is in reach."""
    trend = next(l for l in _story(df, tmp_path, "2023-04-21") if l["role"] == "the trend")
    assert "further than this move can reach" in trend["how"], trend["how"]
    near = next(l for l in _story(df, tmp_path, "2026-02-13") if l["role"] == "the trend")
    assert "further than this move can reach" not in near["how"], near["how"]
    assert "the trend" in [l["role"] for l in _story(df, tmp_path, "2023-03-24")]


def test_sideways_also_draws_the_trend_before_the_range(df, tmp_path):
    """2022-10-14: a three-week range inside the 2022 bear market hid his "clear trend" (his line is
    at 20,739 that day). "if current is sideways calculate also the previous trend which is what was
    before the first peak or valley in the pipe" (2026-10-07). 2025-07-04 stays sideways."""
    lines = {l["role"]: l["price"] for l in _story(df, tmp_path, "2022-10-14")}
    assert abs(lines["the previous trend"] / 20_739 - 1) * 100 <= HIS_ZONE_PCT, lines
    assert not any("trend" in l["role"] for l in _story(df, tmp_path, "2025-07-04"))


def test_a_level_comes_from_a_previous_resistance_not_the_move_itself(df, tmp_path):
    """2022-07-22: the resistance above was 24,286 - a 2020 wiggle plus this move's own high two
    days earlier. "the current resistance is not from a previous resistance at all. the point it
    touched wasnt a resistance." His line is flat at ~29,000 (2020-12-24 -> 2022-08-24)."""
    lines = {l["role"]: l["price"] for l in _story(df, tmp_path, "2022-07-22")}
    assert abs(lines["resistance above"] / 29_000 - 1) * 100 <= HIS_ZONE_PCT, lines
