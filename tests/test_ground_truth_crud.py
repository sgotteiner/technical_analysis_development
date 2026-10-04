"""
Managing the ground truth after it is recorded (owner, 2026-10-04: "i would like to revisit my
drawings easily... what if i want to edit and fix it? i cant do these stuff right now. read add
remove edit easily. crud principles").

Two things that had no mechanism at all before: fixing a drawing's SHAPE without losing what hangs
off it, and removing a multi-stroke explanation as the one thing he drew.
"""
import pytest
from fastapi.testclient import TestClient
from gt_store import GroundTruth
from scripts.sr_playground import create_app
from setup_charts import setup_chart

LINE = {"kind": "line", "label": "support", "chart": "btc_1d", "note": "the rung below",
        "points": [{"time": 1600000000, "price": 10000.0}, {"time": 1610000000, "price": 30000.0}]}
BOX = {"kind": "box", "label": "flag", "chart": "btc_1d",
       "points": [{"time": 1605000000, "price": 15000.0}, {"time": 1606000000, "price": 18000.0}]}
MOVED = [{"time": 1600000000, "price": 11000.0}, {"time": 1610000000, "price": 31000.0}]


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(setup_chart(), tmp_path / "gt.json"))


def test_fixing_a_shape_keeps_everything_hanging_off_it(tmp_path):
    """A line drawn 2% off used to mean delete and draw again, which lost its label, its note, its
    setup and the verdict that pointed at it. Patching the points keeps all four."""
    store = GroundTruth(tmp_path / "gt.json")
    line = store.add(LINE)
    setup = store.add_setup({"name": "sep setup", "members": [line["id"]]})
    verdict = store.judge({"kind": "level", "verdict": "bad", "price": 72799.0, "at": 1788480000,
                           "replacement": line["id"]})
    fixed = store.update(line["id"], {"points": MOVED})
    assert [p["price"] for p in fixed["points"]] == [11000.0, 31000.0]
    assert (fixed["id"], fixed["label"], fixed["note"]) == (line["id"], "support", "the rung below")
    again = GroundTruth(tmp_path / "gt.json")
    assert again.list_setups()[0]["members"] == [line["id"]] and again.list_setups()[0]["id"] == setup["id"]
    assert again.list_judgements()[0]["replacement"] == line["id"] and again.list_judgements()[0]["id"] == verdict["id"]


def test_a_fixed_shape_is_still_checked_against_its_kind(tmp_path):
    store = GroundTruth(tmp_path / "gt.json")
    box = store.add(BOX)
    with pytest.raises(ValueError):          # a box needs two different prices
        store.update(box["id"], {"points": [{"time": 1605000000, "price": 15000.0},
                                            {"time": 1606000000, "price": 15000.0}]})
    with pytest.raises(ValueError):          # a box is two points, not three
        store.update(box["id"], {"points": BOX["points"] + [{"time": 1607000000, "price": 2.0}]})
    assert store.list()[0]["points"] == [{"time": 1605000000, "price": 15000.0},
                                         {"time": 1606000000, "price": 18000.0}]
    with pytest.raises(KeyError):
        store.update("missing", {"points": MOVED})


def test_a_multi_stroke_explanation_is_removed_as_one_thing(tmp_path):
    """His 8-stroke sketch is one explanation with one note: eight deletes was eight clicks, and
    the setups and verdicts pointing at any stroke are tidied in the same write."""
    store = GroundTruth(tmp_path / "gt.json")
    strokes = store.add_many([{**LINE, "kind": "freehand", "label": "sketch", "group": "g1",
                               "points": [{"time": 1600000000 + i, "price": 100.0 + i} for i in range(5)]}
                              for _ in range(3)])
    other = store.add(LINE)
    store.judge({"kind": "level", "verdict": "bad", "price": 100.0, "at": 1788480000,
                 "replacement": strokes[0]["id"]})
    assert store.delete_group("g1") == 3
    assert [a["id"] for a in store.list()] == [other["id"]]
    assert store.list_judgements()[0]["replacement"] is None
    assert store.delete_group("g1") == 0


def test_the_page_can_fix_and_remove_over_http(client):
    line = client.post("/api/annotations", json=LINE).json()
    fixed = client.patch(f"/api/annotations/{line['id']}", json={"points": MOVED})
    assert fixed.status_code == 200 and fixed.json()["points"][0]["price"] == 11000.0
    assert client.patch(f"/api/annotations/{line['id']}", json={"points": MOVED[:1]}).status_code == 422
    assert client.patch("/api/annotations/nope", json={"points": MOVED}).status_code == 404
    client.post("/api/annotations/group", json={"items": [
        {**LINE, "kind": "freehand", "label": "sketch", "group": "g2",
         "points": [{"time": 1600000000 + i, "price": 100.0 + i} for i in range(4)]} for _ in range(2)]})
    gone = client.delete("/api/annotations/group/g2")
    assert gone.status_code == 200 and gone.json()["deleted"] == 2
    assert client.delete("/api/annotations/group/g2").status_code == 404
    assert [a["id"] for a in client.get("/api/annotations").json()] == [line["id"]]
