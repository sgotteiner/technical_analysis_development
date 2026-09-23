"""
Tests for the swing-points API (routes/sr_playground_routes.py): the peaks and valleys at chosen
sizes, to draw on the chart. The owner, 2026-09-23: "i need to see it. cant decide like that."
"""
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scripts.sr_playground import create_app
from modules.shapes.sr_turning_points import turning_points, PEAK
from modules.shapes.swing_calibration import calibrate_size
from modules.shapes.point_lines import lines_from_points

N = 600


@pytest.fixture
def df():
    c = 100 * np.exp(np.cumsum(np.random.default_rng(11).normal(0, 0.025, N)))
    idx = pd.date_range("2022-01-01", periods=N, freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c}, index=idx)


@pytest.fixture
def client(df, tmp_path):
    return TestClient(create_app(df, tmp_path / "gt.json"))


def test_points_at_a_given_size_are_the_confirmed_turning_points(client, df):
    got = client.post("/api/points", json={"end": 450, "sizes": [0.12]}).json()
    tp = turning_points(df, 0.12)
    want = [i for i, c in zip(tp["idx"], tp["conf"]) if c <= 450]
    group = got["sizes"][0]
    assert group["size"] == 0.12
    assert [p["bar"] for p in group["points"]] == want
    assert all(p["kind"] in ("peak", "valley") for p in group["points"])
    first = group["points"][0]
    assert first["time"] == int(df.index[first["bar"]].timestamp())
    assert first["price"] == pytest.approx(df["High" if first["kind"] == "peak" else "Low"].iloc[first["bar"]])


def test_several_sizes_at_once(client):
    got = client.post("/api/points", json={"end": 500, "sizes": [0.06, 0.12]}).json()
    assert [g["size"] for g in got["sizes"]] == [0.06, 0.12]
    assert len(got["sizes"][0]["points"]) > len(got["sizes"][1]["points"])


def test_a_holding_time_calibrates_the_size(client, df):
    got = client.post("/api/points", json={"end": 500, "target_days": 14}).json()
    want = calibrate_size(df, 500, 14)
    assert got["calibrated"]["size"] == want["size"] and got["calibrated"]["median_days"] == want["median_days"]
    assert [g["size"] for g in got["sizes"]] == [round(want["size"], 4)]


@pytest.mark.parametrize("body", [{"end": N, "sizes": [0.1]}, {"end": 10, "sizes": []},
                                  {"end": 10, "sizes": [0.001]}, {"end": 10, "target_days": 0}])
def test_bad_requests(client, body):
    assert client.post("/api/points", json=body).status_code == 422


def test_levels_come_from_the_recent_points_and_their_history(client, df):
    """The owner's rule (default): a level is a recent point's price; history counts its visits."""
    body = {"end": 550, "sizes": [0.12], "lines": {"tol_pct": 2.0, "min_touches": 2, "top": 5, "anchor_days": 120}}
    group = client.post("/api/points", json=body).json()["sizes"][0]
    assert "lines" not in group and group["levels"] and "trends" in group
    for lv in group["levels"]:
        assert lv["anchor"] >= 550 - 120 + 1                       # every level is anchored recently
        assert lv["touches"] == lv["history"] + sum(1 for p in lv["points"] if p >= 550 - 120 + 1)
    assert [lv["history"] for lv in group["levels"]] == sorted([lv["history"] for lv in group["levels"]], reverse=True)
    for t in group["trends"]:
        assert t["last"] >= 550 - 120 + 1        # still touched now, but it may start much earlier
        assert t["role"] in ("support", "resistance")


def test_lines_through_the_points(client, df):
    body = {"end": 550, "sizes": [0.12], "lines": {"mode": "touches", "tol_pct": 2.0, "min_touches": 3, "top": 5}}
    group = client.post("/api/points", json=body).json()["sizes"][0]
    assert 0 < len(group["lines"]) <= 5
    want = lines_from_points(np.array([p["bar"] for p in group["points"]], dtype=float),
                             np.log(np.array([p["price"] for p in group["points"]])), 2.0, 3, None, 5,
                             550 - 90 + 1)                       # the default anchor: the last 90 days
    assert group["lines"] == want
    assert all(l["touches"] >= 3 for l in group["lines"])
    assert all(max(l["points"]) >= 550 - 90 + 1 for l in group["lines"]), "every line touches a recent point"


def test_lines_only_use_points_up_to_now(client, df):
    body = {"end": 300, "sizes": [0.12], "lines": {"mode": "touches", "tol_pct": 2.0, "min_touches": 2, "top": 3}}
    for line in client.post("/api/points", json=body).json()["sizes"][0]["lines"]:
        assert line["last"] <= 300


def test_a_lookback_limits_the_points_used(client):
    long_body = {"end": 550, "sizes": [0.08], "lines": {"tol_pct": 2.0, "min_touches": 2, "top": 50}}
    short = client.post("/api/points", json={**long_body, "lookback_days": 120}).json()["sizes"][0]
    assert all(p["bar"] >= 550 - 120 for p in short["points"])


def test_too_many_points_for_the_touch_rule_is_refused_with_a_reason(client):
    body = {"end": 550, "sizes": [0.02], "lines": {"mode": "touches", "tol_pct": 2.0, "min_touches": 2}}
    res = client.post("/api/points", json=body)
    assert res.status_code == 422 and "size" in res.json()["detail"].lower()


def test_the_owner_rule_copes_with_many_points(client):
    """Levels only walk the recent points, so a small size is not a problem for them."""
    body = {"end": 550, "sizes": [0.02], "lines": {"tol_pct": 2.0, "min_touches": 2, "anchor_days": 120}}
    res = client.post("/api/points", json=body)
    assert res.status_code == 200 and res.json()["sizes"][0]["levels"]
