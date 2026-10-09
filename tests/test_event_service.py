"""
The events over history (business_logic_services/event_service.py): judged only on what was known
each day, and the candle switch keeps only the events a candle confirms.
"""
import pandas as pd
import pytest
from business_logic_services import line_history
from business_logic_services.event_service import EventFlags, compute_events
from business_logic_services.line_concepts import Concepts
from scripts.sr_playground import load_daily


@pytest.fixture(scope="module")
def short(tmp_path_factory):
    """Lines from 2023-09 only, cached in a temp folder: the same code on a window that runs fast."""
    mp = pytest.MonkeyPatch()
    mp.setattr(line_history, "FIRST_DAY", "2023-09-01")
    mp.setattr(line_history, "CACHE_DIR", str(tmp_path_factory.mktemp("lines")))
    df = load_daily()
    upto = lambda day: df.iloc[:int(df.index.get_indexer([pd.Timestamp(day, tz="UTC")])[0]) + 1]
    yield upto
    mp.undo()


def _keys(events):
    return [(e["bar"], e["type"], e["direction"], round(e.get("line", {}).get("value", 0))) for e in events]


def test_no_event_uses_the_future(short):
    later, cut = short("2024-06-30"), short("2024-03-31")
    known = [e for e in compute_events(later, Concepts(), 0.07, EventFlags(), {}) if e["bar"] < len(cut)]
    assert known and _keys(known) == _keys(compute_events(cut, Concepts(), 0.07, EventFlags(), {}))


def test_the_candle_switch_keeps_only_confirmed_events(short):
    df = short("2024-06-30")
    every = compute_events(df, Concepts(), 0.07, EventFlags(), {})
    pins = compute_events(df, Concepts(), 0.07, EventFlags(candle="pin"), {})
    assert 0 < len(pins) < len(every)
    assert all(e["candle"] == "pin" for e in pins)
    assert set(_keys(pins)) <= set(_keys(every))
