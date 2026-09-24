"""
Tests for the zone API: zones at a swing size and the ladder from the current price.
"""
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scripts.sr_playground import create_app
from business_logic_services.zone_service import zone_view

N = 600


@pytest.fixture
def df():
    c = 100 * np.exp(np.cumsum(np.random.default_rng(12).normal(0, 0.03, N)))
    idx = pd.date_range("2022-01-01", periods=N, freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c}, index=idx)


@pytest.fixture
def client(df, tmp_path):
    return TestClient(create_app(df, tmp_path / "gt.json", presets_path=tmp_path / "p.yaml"))


def test_zones_and_ladder(client, df):
    got = client.post("/api/zones", json={"end": 500, "size": 0.2, "min_visits": 2, "n_each": 3}).json()
    assert got == zone_view(df, 500, 0.2, None, 2, 3)
    assert got["price_now"] == pytest.approx(df["Close"].iloc[500])
    assert all(z["price"] > got["price_now"] for z in got["above"])
    assert all(z["price"] < got["price_now"] for z in got["below"])
    assert all(z["label"] == "resistance" for z in got["above"])
    assert all(z["label"] == "support" for z in got["below"])
    for z in got["zones"]:
        assert z["low"] < z["price"] < z["high"] and z["visits"] >= 2
        assert z["first_time"] <= z["last_time"] and len(z["visit_times"]) == z["touches"]


def test_only_data_up_to_now_is_used(client, df):
    got = client.post("/api/zones", json={"end": 300, "size": 0.2}).json()
    assert got["price_now"] == pytest.approx(df["Close"].iloc[300])
    assert all(z["last_visit"] <= 300 for z in got["zones"])


@pytest.mark.parametrize("body", [{"end": N, "size": 0.2}, {"end": 10, "size": 0},
                                  {"end": 10, "size": 0.2, "n_each": 99}])
def test_bad_requests(client, body):
    assert client.post("/api/zones", json=body).status_code == 422
