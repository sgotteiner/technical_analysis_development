"""
The owner's verdicts on the lines the CODE drew (2026-10-03: "if you want me to see and judge tell
me"). A verdict is ground truth about a line at a date, so a later search with other settings is
scored against it. Store: repositories/sr_verdicts_repo.py, API: /api/judgements.
"""
import json
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from gt_store import GroundTruth
from repositories.sr_verdicts_repo import SAME_LINE_PCT
from scripts.sr_playground import create_app

AT = 1757030400          # a "now" in unix seconds
GOOD = {"kind": "level", "verdict": "good", "price": 72799.0, "at": AT}


@pytest.fixture
def store(tmp_path):
    return GroundTruth(tmp_path / "gt.json")


@pytest.fixture
def client(tmp_path):
    c = 100 * np.exp(np.cumsum(np.random.default_rng(7).normal(0, 0.03, 300)))
    idx = pd.date_range("2022-01-01", periods=300, freq="D", tz="UTC")
    df = pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c}, index=idx)
    return TestClient(create_app(df, tmp_path / "gt.json"))


def test_a_verdict_is_recorded_and_listed(store):
    saved = store.judge(GOOD)
    assert saved["verdict"] == "good" and saved["price"] == 72799.0 and saved["id"]
    assert store.list_judgements() == [saved]


def test_judging_the_same_line_again_replaces_the_verdict(store):
    store.judge(GOOD)
    changed = store.judge({**GOOD, "verdict": "bad", "note": "changed my mind"})
    kept = store.list_judgements()
    assert len(kept) == 1, "changing his mind must leave one truth, not two"
    assert kept[0]["verdict"] == "bad" and kept[0]["note"] == "changed my mind"
    assert kept[0]["id"] == changed["id"]


def test_the_same_line_at_a_slightly_different_price_is_the_same_line(store):
    """Prices shift a little with the settings; the verdict is about the line, not the number."""
    store.judge(GOOD)
    near = GOOD["price"] * (1 + SAME_LINE_PCT / 100 * 0.9)
    store.judge({**GOOD, "price": near, "verdict": "bad"})
    assert len(store.list_judgements()) == 1
    far = GOOD["price"] * (1 + SAME_LINE_PCT / 100 * 3)
    store.judge({**GOOD, "price": far, "verdict": "bad"})
    assert len(store.list_judgements()) == 2, "a line further away is a different line"


def test_a_level_and_a_trend_at_one_price_are_different_lines(store):
    store.judge(GOOD)
    store.judge({**GOOD, "kind": "trend", "verdict": "bad", "slope_pct_day": -0.2})
    assert len(store.list_judgements()) == 2


def test_a_verdict_at_another_date_is_its_own_verdict(store):
    store.judge(GOOD)
    store.judge({**GOOD, "at": AT + 86400 * 7, "verdict": "bad"})
    assert len(store.list_judgements()) == 2, "the same price can be good one week and bad the next"


def test_verdicts_live_beside_the_drawings_in_one_file(store, tmp_path):
    store.add({"kind": "line", "label": "support", "chart": "btc_1d",
               "points": [{"time": AT, "price": 100}, {"time": AT + 86400, "price": 101}]})
    store.judge(GOOD)
    data = json.loads((tmp_path / "gt.json").read_text(encoding="utf-8"))
    assert len(data["annotations"]) == 1 and len(data["judgements"]) == 1
    assert store.list()[0]["label"] == "support", "judging must not disturb the drawings"


def test_settings_are_kept_as_provenance_but_do_not_identify_the_line(store):
    store.judge({**GOOD, "settings": {"size": 0.07, "band": 1.5}})
    store.judge({**GOOD, "verdict": "bad", "settings": {"size": 0.09, "band": 3.0}})
    kept = store.list_judgements()
    assert len(kept) == 1, "the same line judged under other settings is still the same line"
    assert kept[0]["settings"]["size"] == 0.09


def test_a_verdict_can_be_removed(store):
    saved = store.judge(GOOD)
    assert store.unjudge(saved["id"]) is True
    assert store.list_judgements() == []
    assert store.unjudge(saved["id"]) is False


def test_a_bad_verdict_is_refused(store):
    with pytest.raises(ValueError):
        store.judge({**GOOD, "verdict": "meh"})
    with pytest.raises(ValueError):
        store.judge({**GOOD, "kind": "pipe"})
    with pytest.raises(ValueError):
        store.judge({**GOOD, "price": -1})


def _a_drawing(store, label="my line"):
    return store.add({"kind": "line", "label": label, "chart": "btc_1d",
                      "points": [{"time": AT, "price": 100}, {"time": AT + 86400, "price": 101}]})


def test_a_note_can_be_added_to_a_verdict_afterwards(store):
    """He judges first and explains after: "a note option is always good"."""
    saved = store.judge({**GOOD, "verdict": "bad"})
    after = store.annotate_judgement(saved["id"], {"note": "those are 2024 highs, nothing bounced"})
    assert after["note"] == "those are 2024 highs, nothing bounced"
    assert after["verdict"] == "bad", "a note must not disturb the verdict"
    assert len(store.list_judgements()) == 1


def test_a_rejected_line_can_point_at_the_line_he_drew_instead(store):
    drawing = _a_drawing(store, "what it should have been")
    saved = store.judge({**GOOD, "verdict": "bad"})
    after = store.annotate_judgement(saved["id"], {"replacement": drawing["id"]})
    assert after["replacement"] == drawing["id"]


def test_a_replacement_must_be_a_drawing_that_exists(store):
    saved = store.judge({**GOOD, "verdict": "bad"})
    with pytest.raises(ValueError):
        store.annotate_judgement(saved["id"], {"replacement": "nope"})


def test_deleting_the_replacement_drawing_keeps_the_verdict_and_its_note(store):
    drawing = _a_drawing(store)
    saved = store.judge({**GOOD, "verdict": "bad"})
    store.annotate_judgement(saved["id"], {"note": "wrong place", "replacement": drawing["id"]})
    store.delete(drawing["id"])
    left = store.list_judgements()
    assert len(left) == 1 and left[0]["replacement"] is None
    assert left[0]["note"] == "wrong place", "the reason he rejected it outlives the drawing"


def test_re_judging_keeps_nothing_stale_from_the_old_verdict(store):
    saved = store.judge({**GOOD, "verdict": "bad"})
    store.annotate_judgement(saved["id"], {"note": "noise"})
    again = store.judge({**GOOD, "verdict": "good"})
    left = store.list_judgements()
    assert len(left) == 1 and left[0]["verdict"] == "good"
    assert left[0]["note"] == "", "the old reason belonged to the old verdict"
    assert left[0]["id"] == again["id"]


def test_patching_an_unknown_verdict_is_an_error(store):
    with pytest.raises(KeyError):
        store.annotate_judgement("nope", {"note": "x"})


def test_api_notes_a_verdict_and_links_a_replacement(client):
    posted = client.post("/api/judgements", json={**GOOD, "verdict": "bad"}).json()
    drawing = client.post("/api/annotations", json={
        "kind": "line", "label": "instead", "points": [{"time": AT, "price": 100},
                                                       {"time": AT + 86400, "price": 101}]}).json()
    r = client.patch(f"/api/judgements/{posted['id']}",
                     json={"note": "too far from the dots", "replacement": drawing["id"]})
    assert r.status_code == 200 and r.json()["note"] == "too far from the dots"
    assert r.json()["replacement"] == drawing["id"]
    assert client.patch(f"/api/judgements/{posted['id']}", json={"replacement": "nope"}).status_code == 422
    assert client.patch("/api/judgements/nope", json={"note": "x"}).status_code == 404
    assert client.patch(f"/api/judgements/{posted['id']}", json={"verdict": "good"}).status_code == 422


def test_api_records_lists_and_deletes_a_verdict(client):
    assert client.get("/api/judgements").json() == []
    posted = client.post("/api/judgements", json=GOOD).json()
    assert posted["verdict"] == "good" and posted["chart"] == "btc_1d"
    assert len(client.get("/api/judgements").json()) == 1
    assert client.delete(f"/api/judgements/{posted['id']}").status_code == 200
    assert client.get("/api/judgements").json() == []
    assert client.delete(f"/api/judgements/{posted['id']}").status_code == 404


def test_api_refuses_a_bad_verdict(client):
    assert client.post("/api/judgements", json={**GOOD, "verdict": "meh"}).status_code == 422
