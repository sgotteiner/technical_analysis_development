"""
Tests for the setup API (routes/setup_routes.py) through the real playground app: setup groups
(CRUD), the detector's episodes over the whole chart, and each drawn setup's evaluation.
"""
import pytest
from fastapi.testclient import TestClient
from scripts.sr_playground import create_app
from business_logic_services.setup_evaluation import detection_episodes
from setup_charts import setup_chart


@pytest.fixture
def df():
    return setup_chart()


@pytest.fixture
def client(df, tmp_path):
    return TestClient(create_app(df, tmp_path / "gt.json"))


def _t(df, i):
    return int(df.index[i].timestamp())


def test_setup_crud(client, df):
    pts = [{"time": _t(df, 20), "price": 100}, {"time": _t(df, 133), "price": 100}]
    a = client.post("/api/annotations", json={"kind": "line", "label": "resistance", "points": pts}).json()
    s = client.post("/api/setups", json={"name": "s1", "note": "buy the breakout", "members": [a["id"]]})
    assert s.status_code == 200 and s.json()["members"] == [a["id"]]
    sid = s.json()["id"]
    assert [x["id"] for x in client.get("/api/setups").json()] == [sid]
    assert client.patch(f"/api/setups/{sid}", json={"name": "s2"}).json()["name"] == "s2"
    assert client.post("/api/setups", json={"name": "bad", "members": ["nope"]}).status_code == 422
    assert client.patch("/api/setups/nope", json={"name": "x"}).status_code == 404
    assert client.delete(f"/api/setups/{sid}").status_code == 200
    assert client.delete(f"/api/setups/{sid}").status_code == 404


def test_detections_are_the_episodes_over_the_whole_chart(client, df):
    got = client.get("/api/setup-detections").json()
    assert got == detection_episodes(df) and got


def test_drawn_setups_are_evaluated(client, df):
    end = len(df) - 1
    line = client.post("/api/annotations", json={"kind": "line", "label": "resistance", "drawn_at": _t(df, end),
                       "points": [{"time": _t(df, 20), "price": 100}, {"time": _t(df, end), "price": 100}]}).json()
    box = client.post("/api/annotations", json={"kind": "box", "label": "bull flag", "drawn_at": _t(df, end),
                      "points": [{"time": _t(df, 110), "price": 70}, {"time": _t(df, end), "price": 98}]}).json()
    s = client.post("/api/setups", json={"name": "s", "members": [line["id"], box["id"]]}).json()
    ev = client.get("/api/setups/evaluation").json()
    assert list(ev) == [s["id"]] and ev[s["id"]]["found"] is True
