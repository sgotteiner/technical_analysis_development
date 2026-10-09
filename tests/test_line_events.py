"""
The stars: breakout / retest / fakeout at the lines on the screen, during the move running now
(business_logic_services/line_events.py), at his dates.
"""
import pandas as pd
from fastapi.testclient import TestClient
from scripts.sr_playground import create_app, load_daily


def _stars(df, tmp_path, date):
    gt = tmp_path / "gt.json"
    gt.write_text('{"annotations": [], "setups": [], "judgements": []}')
    end = int(df.index.get_indexer([pd.Timestamp(date, tz="UTC")])[0])
    g = TestClient(create_app(df, str(gt))).post("/api/points", json={
        "end": end, "sizes": [0.07], "lines": {"mode": "owner"}}).json()["sizes"][0]
    return [(e["date"], e["type"], e["direction"], e["role"]) for e in g["line_events"]]


def test_his_2026_08_19_breakout_through_the_trend_line(tmp_path):
    """His confluence breakout: one candle closed above the falling trend line (docs: Events)."""
    assert ("2026-08-19", "breakout", "up", "the trend") in _stars(load_daily(), tmp_path, "2026-09-04")


def test_no_star_when_nothing_happened_at_todays_lines(tmp_path):
    """2025-12-28: since the move began (12-09) price stayed between 82k and 93.8k."""
    assert _stars(load_daily(), tmp_path, "2025-12-28") == []
