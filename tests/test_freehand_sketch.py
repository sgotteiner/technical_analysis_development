"""
Freehand sketches (owner, 2026-10-03: "i would love another tool to press ctrl and draw with the
mouse and note the draw. i want to be able to explain to you better").

A sketch is an EXPLANATION, not a line: it is stored beside the drawings but must never be read as
ground truth for the line layer, or it would be scored as a line he drew.
"""
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from business_logic_services.ground_truth_score import score_against_drawings
from repositories.sr_annotation_repo import AnnotationStore
from schemas.sr_playground_schema import MAX_SKETCH_POINTS
from scripts.sr_playground import create_app

T0 = 1757030400
path = lambda n: [{"time": T0 + i * 86400, "price": 60000 + i * 100} for i in range(n)]
SKETCH = {"kind": "freehand", "label": "sketch", "points": path(40),
          "note": "this is the peak I meant"}


@pytest.fixture
def store(tmp_path):
    return AnnotationStore(tmp_path / "gt.json")


@pytest.fixture
def client(tmp_path):
    c = 100 * np.exp(np.cumsum(np.random.default_rng(3).normal(0, 0.03, 300)))
    idx = pd.date_range("2022-01-01", periods=300, freq="D", tz="UTC")
    df = pd.DataFrame({"Open": c, "High": c * 1.01, "Low": c * 0.99, "Close": c}, index=idx)
    return TestClient(create_app(df, tmp_path / "gt.json"))


def test_a_sketch_keeps_every_point_of_the_path(store):
    saved = store.add(SKETCH)
    assert saved["kind"] == "freehand" and len(saved["points"]) == 40
    assert saved["note"] == "this is the peak I meant"


def test_a_sketch_needs_at_least_two_points(store):
    with pytest.raises(ValueError):
        store.add({**SKETCH, "points": path(1)})


def test_a_very_long_path_is_refused_rather_than_stored(store):
    with pytest.raises(ValueError):
        store.add({**SKETCH, "points": path(MAX_SKETCH_POINTS + 1)})


def test_lines_and_boxes_are_still_exactly_two_points(store):
    with pytest.raises(ValueError):
        store.add({"kind": "line", "label": "support", "points": path(5)})
    with pytest.raises(ValueError):
        store.add({"kind": "box", "label": "flag", "points": path(3)})
    two = store.add({"kind": "line", "label": "support", "points": path(2)})
    assert len(two["points"]) == 2


def test_a_sketch_is_never_scored_as_a_line_he_drew():
    """The whole risk: an explanation counted as ground truth would be a line he never meant."""
    drawn_line = {"kind": "line", "label": "support",
                  "points": [{"time": T0, "price": 60000}, {"time": T0 + 86400, "price": 60000}]}
    sketch = {**SKETCH, "points": path(30)}
    found = {"zones": [{"price": 60000}], "trends": []}
    only_line = score_against_drawings([drawn_line], found, 61000)
    with_sketch = score_against_drawings([drawn_line, sketch], found, 61000)
    assert with_sketch["total"] == only_line["total"] == 1
    assert with_sketch["found"] == 1 and not with_sketch["extra"]


def test_the_note_can_be_edited_after_drawing(store):
    saved = store.add({**SKETCH, "note": ""})
    after = store.update(saved["id"], {"note": "the 80k peak I was referring to"})
    assert after["note"] == "the 80k peak I was referring to"


def test_api_saves_a_sketch_and_lists_it_with_the_drawings(client):
    posted = client.post("/api/annotations", json=SKETCH)
    assert posted.status_code == 200, posted.text
    assert posted.json()["kind"] == "freehand"
    listed = client.get("/api/annotations").json()
    assert len(listed) == 1 and len(listed[0]["points"]) == 40
    assert client.post("/api/annotations", json={**SKETCH, "points": path(1)}).status_code == 422


def test_a_sketch_can_be_deleted_like_any_drawing(client):
    sid = client.post("/api/annotations", json=SKETCH).json()["id"]
    assert client.delete(f"/api/annotations/{sid}").status_code == 200
    assert client.get("/api/annotations").json() == []


# ---- several strokes, one note; and keep vs just-showing-you (owner, 2026-10-03) ----

def _group(n, **kw):
    return [{**SKETCH, "points": path(6 + i), "group": "g1", **kw} for i in range(n)]


def test_several_strokes_share_one_note_and_one_group(store):
    saved = store.add_many(_group(3, note="the peak I mean"))
    assert len(saved) == 3
    assert {s["group"] for s in saved} == {"g1"}
    assert all(s["note"] == "the peak I mean" for s in saved)
    assert len(store.list()) == 3


def test_a_group_is_all_or_nothing(store):
    """A half-saved explanation is worse than none: the drawing would be missing its other half."""
    bad = _group(2) + [{**SKETCH, "points": path(1), "group": "g1"}]
    with pytest.raises(ValueError):
        store.add_many(bad)
    assert store.list() == [], "nothing may be written when one stroke is invalid"


def test_a_sketch_is_kept_unless_it_says_otherwise(store):
    assert store.add(SKETCH)["purpose"] == "keep"


def test_clearing_only_removes_what_he_was_just_showing(store):
    store.add({**SKETCH, "purpose": "ask", "note": "look here"})
    store.add({**SKETCH, "purpose": "ask", "note": "and here"})
    mine = store.add({**SKETCH, "purpose": "keep", "note": "worth keeping"})
    drawn = store.add({"kind": "line", "label": "support", "points": path(2)})
    assert store.clear_asked() == 2
    left = {a["id"] for a in store.list()}
    assert left == {mine["id"], drawn["id"]}, "his own drawings and kept sketches stay"
    assert store.clear_asked() == 0


def test_clearing_does_not_leave_a_verdict_pointing_at_a_deleted_sketch(store):
    sk = store.add({**SKETCH, "purpose": "ask"})
    j = store.judge({"kind": "level", "verdict": "bad", "price": 100.0, "at": T0})
    store.annotate_judgement(j["id"], {"replacement": sk["id"], "note": "see the sketch"})
    store.clear_asked()
    left = store.list_judgements()[0]
    assert left["replacement"] is None and left["note"] == "see the sketch"


def test_api_saves_a_group_and_clears_the_asked_ones(client):
    r = client.post("/api/annotations/group", json={"items": _group(3, purpose="ask", note="n")})
    assert r.status_code == 200 and len(r.json()) == 3
    client.post("/api/annotations", json={**SKETCH, "purpose": "keep"})
    assert len(client.get("/api/annotations").json()) == 4
    assert client.delete("/api/annotations/asked").json() == {"deleted": 3}
    left = client.get("/api/annotations").json()
    assert len(left) == 1 and left[0]["purpose"] == "keep"


def test_api_refuses_a_group_with_a_bad_stroke(client):
    bad = {"items": _group(2) + [{**SKETCH, "points": path(1)}]}
    assert client.post("/api/annotations/group", json=bad).status_code == 422
    assert client.get("/api/annotations").json() == []
