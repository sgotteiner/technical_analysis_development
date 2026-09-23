"""
Tests for saved playground presets (repositories/sr_preset_repo.py). The owner, 2026-09-24:
"i want a dedicated yaml file or whatever along with the code they worked on. what if we change
the code or settings? we lose it?"
A preset is a named set of playground settings + the git commit they were produced on, in
config/sr_presets.yaml, so a state can always be brought back with its code.
"""
import pytest
import yaml
from repositories.sr_preset_repo import PresetStore, SHIPPED

SETTINGS = {"sizesText": "8", "anchorDays": 120, "minTouches": 3, "maxHistory": 2, "tolPct": 1.5,
            "top": 6, "targetDays": 14, "mode": "owner"}


@pytest.fixture
def store(tmp_path):
    return PresetStore(tmp_path / "presets.yaml", commit="abc1234")


def test_empty_when_no_file(store):
    assert store.list() == []


def test_save_records_the_settings_and_the_commit(store, tmp_path):
    saved = store.save("good lines", SETTINGS, note="nice dots and lines")
    assert saved["name"] == "good lines" and saved["settings"] == SETTINGS
    assert saved["commit"] == "abc1234" and saved["saved_at"] and saved["note"] == "nice dots and lines"
    on_disk = yaml.safe_load((tmp_path / "presets.yaml").read_text(encoding="utf-8"))
    assert on_disk["presets"][0]["settings"]["anchorDays"] == 120


def test_presets_are_readable_by_name_and_persist(store, tmp_path):
    store.save("a", SETTINGS)
    store.save("b", {**SETTINGS, "anchorDays": 60})
    again = PresetStore(tmp_path / "presets.yaml", commit="other")
    assert [p["name"] for p in again.list()] == ["a", "b"]
    assert again.get("b")["settings"]["anchorDays"] == 60
    assert again.get("nope") is None


def test_saving_the_same_name_keeps_the_older_one_as_a_version(store):
    store.save("mine", SETTINGS)
    store.save("mine", {**SETTINGS, "tolPct": 2.0})
    names = [p["name"] for p in store.list()]
    assert names.count("mine") == 1 and len([n for n in names if n.startswith("mine ")]) == 1
    assert store.get("mine")["settings"]["tolPct"] == 2.0     # the newest keeps the plain name


def test_a_preset_needs_a_name_and_settings(store):
    for bad in (("", SETTINGS), ("x", {}), ("x", {"nope": 1})):
        with pytest.raises(ValueError):
            store.save(*bad)


def test_the_shipped_file_holds_the_approved_state():
    """The state the owner approved on 2026-09-24 must be in the repo, with its commit."""
    presets = PresetStore(SHIPPED).list()
    assert presets, f"{SHIPPED} must ship with the approved preset"
    first = presets[0]
    assert first["commit"] and first["settings"]["anchorDays"] == 120
    assert (first["settings"]["minTouches"], first["settings"]["maxHistory"]) == (3, 2)
    assert first["settings"]["sizesText"] == "8" and first["settings"]["mode"] == "owner"
