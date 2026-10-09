"""
The line concepts as switches (business_logic_services/line_concepts.py), at his date 2026-09-04.
He asked for two things (2026-10-08): to choose the concepts that make the lines, and to see what
made each line - "which peaks and valleys it used, scores, whatever".
"""
import pytest
import pandas as pd
from business_logic_services.line_concepts import Concepts, concept_lines
from scripts.sr_playground import load_daily


@pytest.fixture(scope="module")
def at():
    df, cache = load_daily(), {}
    end = int(df.index.get_indexer([pd.Timestamp("2026-09-04", tz="UTC")])[0])
    return lambda **flags: concept_lines(df, end, Concepts(**flags), 0.07, cache)


def _prices(g):
    return sorted(round(l["price"]) for l in g["levels"])


@pytest.mark.parametrize("flag, other", [("swings", "pivots"), ("swings", "atr"), ("group", "off"),
                                         ("band", "range"), ("pick", "nearest"), ("pick", "strongest")])
def test_each_switch_changes_the_lines(at, flag, other):
    assert _prices(at(**{flag: other})) != _prices(at())


def test_the_trend_switch(at):
    assert at(trend="off", pick="nearest")["trends"] == [] and at(pick="nearest")["trends"]


def test_each_line_says_what_made_it(at):
    g = at(pick="nearest", per_side=2)
    for line in g["story"]["lines"]:
        assert line["dates"], line["role"]                       # the peaks and valleys it used
        if line["kind"] == "level":
            assert "Score" in line["how"] and "Kept by" in line["how"], line["how"]
            assert set(line["parts"]) == {"pivots", "bars", "sweeps"}
