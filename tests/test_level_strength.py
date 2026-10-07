"""
The strength score (business_logic_services/level_strength.py): the weights come from a measurement,
so these tests pin what the measurement said, not a preference.
"""
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient
from business_logic_services.level_strength import MEAN, STRONG_FROM, score
from scripts.sr_playground import create_app, load_daily

PAGE = {"mode": "owner", "tol_pct": 1.5, "min_touches": 3, "top": 6, "anchor_days": 120,
        "max_history": 2, "merge_pct": 0, "targets_each_way": 2, "min_visits": 2}


def test_an_average_level_is_a_coin_flip():
    """At the average of every feature the score is the base rate the study measured (~50%)."""
    assert abs(score(MEAN) - 0.5) < 0.01


def test_the_directions_are_the_measured_ones():
    """Recent and a big move afterwards raise it; a high share of held visits lowers it - the
    measured surprise (levels broken before turned slightly MORE often, the flip)."""
    base = list(MEAN)
    recent = base.copy(); recent[0] -= 1.0             # age_log down = more recent
    reacted = base.copy(); reacted[6] += 1.0           # a bigger move afterwards
    held_more = base.copy(); held_more[5] += 0.2       # a higher share of held visits
    assert score(recent) > score(base)
    assert score(reacted) > score(base)
    assert score(held_more) < score(base)


def test_every_line_on_the_card_says_its_strength(tmp_path):
    df = load_daily()
    end = int(df.index.get_indexer([pd.Timestamp("2022-07-22", tz="UTC")])[0])
    got = TestClient(create_app(df, tmp_path / "gt.json")).post(
        "/api/points", json={"end": end, "sizes": [0.07], "lines": PAGE}).json()["sizes"][0]
    assert all("strength" in lv and 0 < lv["strength"] < 1 for lv in got["levels"])
    levels = [l for l in got["story"]["lines"] if l["role"] != "the trend"]
    assert levels and all("Strength: " in l["how"] for l in levels)
    assert all("Price held at it" in l["how"] for l in levels)     # held AND broken, both shown
    assert STRONG_FROM > 0.5
