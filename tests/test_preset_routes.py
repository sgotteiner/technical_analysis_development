"""
Tests for the preset API: list the saved playground states and save the current one with the
commit it was produced on.
"""
import pytest
from fastapi.testclient import TestClient
from scripts.sr_playground import create_app
from setup_charts import setup_chart

SETTINGS = {"sizesText": "8", "anchorDays": 120, "minTouches": 3, "maxHistory": 2, "tolPct": 1.5,
            "top": 6, "targetDays": 14, "mode": "owner"}


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(setup_chart(), tmp_path / "gt.json", presets_path=tmp_path / "presets.yaml"))


def test_presets_start_empty_and_can_be_saved(client):
    assert client.get("/api/presets").json() == []
    made = client.post("/api/presets", json={"name": "mine", "settings": SETTINGS, "note": "good"})
    assert made.status_code == 200
    body = made.json()
    assert body["name"] == "mine" and body["settings"] == SETTINGS and body["note"] == "good"
    assert "commit" in body and "saved_at" in body
    assert [p["name"] for p in client.get("/api/presets").json()] == ["mine"]


def test_bad_presets_are_refused(client):
    assert client.post("/api/presets", json={"name": "", "settings": SETTINGS}).status_code == 422
    assert client.post("/api/presets", json={"name": "x", "settings": {"nope": 1}}).status_code == 422


def test_the_shipped_presets_are_served_by_default(tmp_path):
    """With no path given the app serves config/sr_presets.yaml, the one in the repo."""
    client = TestClient(create_app(setup_chart(), tmp_path / "gt.json"))
    names = [p["name"] for p in client.get("/api/presets").json()]
    assert any("good lines" in n for n in names), names
