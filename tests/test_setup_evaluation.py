"""
Tests for matching detected setups with the owner's drawn setups
(business_logic_services/setup_evaluation.py). A drawn setup is found when, on the bar it was
drawn at, the detector has a setup whose resistance is within 2% of the drawn line there and whose
flag span (pole start -> now) overlaps the drawn flag box by >= 50% of their union in time.
"""
import numpy as np
from business_logic_services.setup_evaluation import evaluate_setup, resistance_flag_setups, detection_episodes
from repositories.sr_annotation_repo import AnnotationStore
from setup_charts import setup_chart


def _t(df, i):
    return int(df.index[i].timestamp())


def _setup(df, line_price=100.0, box=(110, 133)):
    end = len(df) - 1
    line = {"kind": "line", "label": "resistance", "points": [{"time": _t(df, 20), "price": line_price},
                                                              {"time": _t(df, end), "price": line_price}]}
    flag = {"kind": "box", "label": "bull flag", "points": [{"time": _t(df, box[0]), "price": 70},
                                                            {"time": _t(df, box[1]), "price": 98}]}
    return {"name": "synthetic", "drawings": [{**line, "drawn_at": _t(df, end)}, {**flag, "drawn_at": _t(df, end)}]}


def test_a_matching_drawing_is_found():
    df = setup_chart()
    res = evaluate_setup(df, _setup(df))
    assert res["found"] and abs(res["line_gap"]) < 1e-9 and res["flag_overlap"] >= 0.5


def test_a_line_drawn_elsewhere_is_not_found():
    df = setup_chart()
    res = evaluate_setup(df, _setup(df, line_price=90.0))
    assert not res["found"] and res["line_gap"] > np.log(1.02)


def test_a_box_drawn_elsewhere_is_not_found():
    df = setup_chart()
    assert not evaluate_setup(df, _setup(df, box=(20, 60)))["found"]


def test_only_owner_setups_with_a_resistance_line_and_a_flag_box_are_checked(tmp_path):
    store = AnnotationStore(tmp_path / "gt.json")
    pts = [{"time": 1600000000, "price": 100}, {"time": 1610000000, "price": 101}]
    line, flag = store.add({"kind": "line", "label": "Resistance", "points": pts}), store.add({"kind": "box", "label": "bull flag", "points": pts})
    other = store.add({"kind": "box", "label": "cup", "points": pts})
    store.add_setup({"name": "ok", "members": [line["id"], flag["id"]]})
    store.add_setup({"name": "no flag", "members": [line["id"], other["id"]]})
    store.add_setup({"name": "claude's", "members": [line["id"], flag["id"]], "author": "claude"})
    assert [s["name"] for s in resistance_flag_setups(store)] == ["ok"]


def test_detection_episodes_carry_dates_lines_and_boxes():
    df = setup_chart()
    eps = detection_episodes(df)
    last = eps[-1]
    assert last["last"] == len(df) - 1 and last["last_date"] == str(df.index[-1].date())
    assert last["line"]["points"][1]["price"] > 0 and last["box"]["points"][0]["time"] == _t(df, last["flag"]["pole_start"])
