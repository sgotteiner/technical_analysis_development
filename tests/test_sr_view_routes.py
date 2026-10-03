"""
Tests for the playground HTTP API (routes/sr_view_routes.py), through the real app that
scripts/sr_playground.py serves: page, candles, defaults, live view, and ground-truth CRUD.
"""
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from scripts.sr_playground import create_app
from modules.shapes.sr_settings import DEFAULT_LEVELS, DEFAULT_RULES
from business_logic_services.sr_pipe_view import playground_view

N = 460


@pytest.fixture
def df():
    c = 100 * np.exp(np.cumsum(np.random.default_rng(50).normal(0, 0.03, N)))
    idx = pd.date_range("2022-01-01", periods=N, freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c}, index=idx)


@pytest.fixture
def client(df, tmp_path):
    return TestClient(create_app(df, tmp_path / "gt.json"))


def test_page_and_chart_library_are_served(client):
    page = client.get("/")
    assert page.status_code == 200 and "S/R Playground" in page.text
    assert client.get("/ui/lightweight-charts.js").status_code == 200


def test_candles_and_defaults(client, df):
    candles = client.get("/api/candles").json()
    assert len(candles) == N and candles[0]["time"] == int(df.index[0].timestamp())
    assert candles[5]["high"] == pytest.approx(df["High"].iloc[5])
    d = client.get("/api/defaults").json()
    assert d["levels"] == DEFAULT_LEVELS and d["rules"]["touch_pct"] == DEFAULT_RULES.touch_pct
    assert d["chart"] == "btc_1d" and d["labels"]


def test_view_matches_the_service(client, df):
    body = {"end": 450, "levels": {"a": {"period": 150, "magnitude": 0.1}}, "rules": {"both_sides": False},
            "pairs": 2, "singles": 3}
    got = client.post("/api/view", json=body)
    assert got.status_code == 200
    from modules.shapes.sr_settings import SRRules
    assert got.json() == playground_view(df, 450, body["levels"], SRRules(both_sides=False), 2, 3)


@pytest.mark.parametrize("body", [
    {"end": N, "levels": DEFAULT_LEVELS},                                  # beyond the data
    {"end": 100, "levels": {"a": {"period": 100, "magnitude": -1}}},
    {"end": 100, "levels": DEFAULT_LEVELS, "rules": {"touch_pct": -2}},
    {"end": 100, "levels": DEFAULT_LEVELS, "pairs": 99},
])
def test_view_rejects_bad_requests(client, body):
    assert client.post("/api/view", json=body).status_code == 422


def test_annotation_crud(client, tmp_path):
    ann = {"kind": "box", "label": "flag", "points": [{"time": 1650000000, "price": 100}, {"time": 1651000000, "price": 120}]}
    made = client.post("/api/annotations", json=ann)
    assert made.status_code == 200 and made.json()["chart"] == "btc_1d"
    aid = made.json()["id"]
    assert [a["id"] for a in client.get("/api/annotations").json()] == [aid]
    assert client.patch(f"/api/annotations/{aid}", json={"label": "pennant"}).json()["label"] == "pennant"
    assert (tmp_path / "gt.json").exists()
    assert client.post("/api/annotations", json={**ann, "kind": "circle"}).status_code == 422
    assert client.patch("/api/annotations/nope", json={"label": "x"}).status_code == 404
    assert client.delete(f"/api/annotations/{aid}").status_code == 200
    assert client.delete(f"/api/annotations/{aid}").status_code == 404
    assert client.get("/api/annotations").json() == []
