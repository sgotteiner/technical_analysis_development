"""
Tests for setup groups in the ground-truth store (repositories/sr_setups_repo.py).
Owner, 2026-09-22: "unite several drawings to a setup group and an annotation how i would trade
that" — a setup = a name, a note on how to trade it, and its member drawings (lines, pattern
boxes, retest / fakeout boxes). Drawings and setups record who made them (owner or Claude): only
the owner's count as ground truth.
"""
import json
import pytest
from gt_store import GroundTruth

LINE = {"kind": "line", "label": "resistance", "points": [{"time": 1600000000, "price": 100.0}, {"time": 1610000000, "price": 101.0}]}
BOX = {"kind": "box", "label": "bull flag", "points": [{"time": 1605000000, "price": 80.0}, {"time": 1606000000, "price": 99.0}]}


@pytest.fixture
def store(tmp_path):
    return GroundTruth(tmp_path / "gt.json")


def test_old_file_without_setups_reads_as_no_setups(tmp_path):
    path = tmp_path / "gt.json"
    path.write_text(json.dumps({"annotations": []}), encoding="utf-8")
    assert GroundTruth(path).list_setups() == []


def test_drawings_record_the_author(store):
    assert store.add(LINE)["author"] == "owner"
    assert store.add({**BOX, "author": "claude"})["author"] == "claude"
    with pytest.raises(ValueError):
        store.add({**BOX, "author": "someone"})


def test_setup_groups_drawings_with_a_trading_note(store, tmp_path):
    a, b = store.add(LINE), store.add(BOX)
    s = store.add_setup({"name": "BTC resistance + bull flag", "note": "buy the breakout", "members": [a["id"], b["id"]]})
    assert s["id"] and s["author"] == "owner" and s["members"] == [a["id"], b["id"]]
    again = GroundTruth(tmp_path / "gt.json")
    assert again.list_setups() == [s] and len(again.list()) == 2


def test_setup_members_must_exist(store):
    with pytest.raises(ValueError):
        store.add_setup({"name": "x", "members": ["nope"]})


def test_update_setup_name_note_and_members(store):
    a, b = store.add(LINE), store.add(BOX)
    s = store.add_setup({"name": "x", "members": [a["id"]]})
    s2 = store.update_setup(s["id"], {"name": "y", "note": "retest entry", "members": [a["id"], b["id"]]})
    assert (s2["name"], s2["note"], s2["members"]) == ("y", "retest entry", [a["id"], b["id"]])
    with pytest.raises(ValueError):
        store.update_setup(s["id"], {"members": ["nope"]})
    with pytest.raises(KeyError):
        store.update_setup("missing", {"name": "z"})


def test_deleting_a_drawing_removes_it_from_its_setups(store):
    a, b = store.add(LINE), store.add(BOX)
    s = store.add_setup({"name": "x", "members": [a["id"], b["id"]]})
    store.delete(a["id"])
    assert store.list_setups()[0]["members"] == [b["id"]]


def test_deleting_a_setup_keeps_its_drawings(store):
    a = store.add(LINE)
    s = store.add_setup({"name": "x", "members": [a["id"]]})
    assert store.delete_setup(s["id"]) is True and store.delete_setup(s["id"]) is False
    assert store.list_setups() == [] and [x["id"] for x in store.list()] == [a["id"]]


def test_setup_with_members_resolves_the_drawings(store):
    a, b = store.add(LINE), store.add(BOX)
    s = store.add_setup({"name": "x", "members": [b["id"], a["id"]]})
    full = store.setups_with_members()
    assert [m["id"] for m in full[0]["drawings"]] == [b["id"], a["id"]] and full[0]["id"] == s["id"]
