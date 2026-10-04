"""
What the system relies on, per drawing (business_logic_services/ground_truth_use.py).

Owner, 2026-10-04: "i would like to revisit my drawings easily so i could see the ground truth the
system relies on." The answer must come from the code that READS the drawings, so these tests pin
that a sketch is told apart from a scored line, and that a setup the detector cannot read does not
claim its members are read.
"""
import pytest
from fastapi.testclient import TestClient
from business_logic_services.ground_truth_use import DETECTOR, EXPLAINS, SCORED, usage
from gt_store import GroundTruth
from scripts.sr_playground import create_app
from setup_charts import setup_chart

PTS = [{"time": 1600000000, "price": 100.0}, {"time": 1610000000, "price": 100.0}]
BOX_PTS = [{"time": 1605000000, "price": 70.0}, {"time": 1606000000, "price": 98.0}]


def _store(tmp_path):
    return GroundTruth(tmp_path / "gt.json")


def test_lines_score_sketches_only_explain(tmp_path):
    store = _store(tmp_path)
    line = store.add({"kind": "line", "label": "current resistance", "points": PTS})
    box = store.add({"kind": "box", "label": "bull flag", "points": BOX_PTS})
    sketch = store.add({"kind": "freehand", "label": "sketch", "group": "g1",
                        "points": [{"time": 1600000000 + i, "price": 100.0} for i in range(4)]})
    got = usage(store.list(), store.setups_with_members())
    assert got[line["id"]]["uses"] == [SCORED] and got[line["id"]]["scored"] is True
    assert got[box["id"]]["uses"] == [EXPLAINS] and got[box["id"]]["scored"] is False
    assert got[sketch["id"]]["uses"] == [EXPLAINS]
    assert all(g["setup"] is None for g in got.values())


def test_a_setup_the_detector_can_read_marks_the_two_drawings_it_reads(tmp_path):
    store = _store(tmp_path)
    line = store.add({"kind": "line", "label": "current resistance", "points": PTS})
    box = store.add({"kind": "box", "label": "bull flag", "points": BOX_PTS})
    sketch = store.add({"kind": "freehand", "label": "why", "points": PTS})
    setup = store.add_setup({"name": "sep", "members": [line["id"], box["id"], sketch["id"]]})
    got = usage(store.list(), store.setups_with_members())
    assert got[line["id"]]["uses"] == [SCORED, DETECTOR]
    assert got[box["id"]]["uses"] == [DETECTOR]
    assert got[sketch["id"]]["uses"] == [EXPLAINS]      # in the setup, read by nothing
    assert {g["setup_name"] for g in got.values()} == {"sep"}
    assert got[line["id"]]["setup"] == setup["id"]


def test_a_setup_without_the_pair_claims_nothing(tmp_path):
    """His own setup has a resistance line and no flag box, so the detector reads neither - which
    is why its evaluation card has always been empty."""
    store = _store(tmp_path)
    line = store.add({"kind": "line", "label": "current resistance", "points": PTS})
    store.add_setup({"name": "lines only", "members": [line["id"]]})
    got = usage(store.list(), store.setups_with_members())
    assert got[line["id"]]["uses"] == [SCORED]         # scored, but not by the setup detector
    assert got[line["id"]]["setup_name"] == "lines only"


def test_the_page_can_ask_over_http(tmp_path):
    client = TestClient(create_app(setup_chart(), tmp_path / "gt.json"))
    line = client.post("/api/annotations", json={"kind": "line", "label": "resistance", "points": PTS}).json()
    got = client.get("/api/ground-truth/usage")
    assert got.status_code == 200 and got.json()[line["id"]]["uses"] == [SCORED]
