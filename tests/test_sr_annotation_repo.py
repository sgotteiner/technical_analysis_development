"""
Tests for the ground-truth store (repositories/sr_annotation_repo.py): the owner's own lines and
pattern boxes, drawn in the playground, saved to a JSON file so the shape blocks can be tested
against them later (owner, 2026-09-22: "his drawings become ground truth for the shape blocks").
"""
import json
import pytest
from repositories.sr_annotation_repo import AnnotationStore

LINE = {"kind": "line", "label": "support", "chart": "btc_1d",
        "points": [{"time": 1600000000, "price": 10000.0}, {"time": 1610000000, "price": 30000.0}]}
BOX = {"kind": "box", "label": "flag", "chart": "btc_1d", "note": "bull flag after the breakout",
       "drawn_at": 1612000000,
       "points": [{"time": 1605000000, "price": 15000.0}, {"time": 1606000000, "price": 18000.0}]}


def test_empty_when_no_file(tmp_path):
    assert AnnotationStore(tmp_path / "gt.json").list() == []


def test_add_assigns_id_and_persists(tmp_path):
    path = tmp_path / "sub" / "gt.json"
    a = AnnotationStore(path).add(LINE)
    b = AnnotationStore(path).add(BOX)
    assert a["id"] != b["id"] and a["created"]
    again = AnnotationStore(path).list()
    assert [x["id"] for x in again] == [a["id"], b["id"]]
    assert again[1]["note"] == BOX["note"] and again[1]["drawn_at"] == BOX["drawn_at"]
    assert json.loads(path.read_text(encoding="utf-8"))["annotations"] == again


def test_update_changes_label_and_note_only(tmp_path):
    store = AnnotationStore(tmp_path / "gt.json")
    a = store.add(LINE)
    b = store.update(a["id"], {"label": "resistance", "note": "flipped"})
    assert (b["label"], b["note"], b["points"], b["id"]) == ("resistance", "flipped", a["points"], a["id"])
    with pytest.raises(ValueError):
        store.update(a["id"], {"id": "x"})
    with pytest.raises(KeyError):
        store.update("missing", {"label": "x"})


def test_delete(tmp_path):
    store = AnnotationStore(tmp_path / "gt.json")
    a, b = store.add(LINE), store.add(BOX)
    assert store.delete(a["id"]) is True and store.delete(a["id"]) is False
    assert [x["id"] for x in AnnotationStore(tmp_path / "gt.json").list()] == [b["id"]]


@pytest.mark.parametrize("bad", [
    {**LINE, "kind": "circle"},
    {**LINE, "label": ""},
    {**LINE, "points": LINE["points"][:1]},
    {**LINE, "points": [{"time": 1, "price": -5}, {"time": 2, "price": 5}]},
    {**BOX, "points": [{"time": 5, "price": 1}, {"time": 5, "price": 2}]},     # zero-width box
])
def test_rejects_invalid_annotations(tmp_path, bad):
    store = AnnotationStore(tmp_path / "gt.json")
    with pytest.raises(ValueError):
        store.add(bad)
    assert store.list() == []
