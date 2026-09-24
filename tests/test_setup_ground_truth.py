"""
Ground-truth test: every setup the OWNER drew (data/ground_truth/sr_annotations.json) that holds a
resistance line and a bull-flag box must be found by the detector on the day he drew it ("now").
Found = a setup on that bar whose resistance is within 2% of his line there, and whose flag span
(pole start -> now) overlaps his box by >= 50% of their union in time (business_logic_services/
setup_evaluation.py). New owner setups of this kind are picked up automatically.
"""
import os
import pytest
from business_logic_services.setup_evaluation import resistance_flag_setups, evaluate_setup
from repositories.sr_annotation_repo import AnnotationStore
from scripts.sr_playground import load_daily, DATA, GROUND_TRUTH

pytestmark = pytest.mark.skipif(not (os.path.exists(DATA) and os.path.exists(GROUND_TRUTH)), reason="no local data")
SETUPS = resistance_flag_setups(AnnotationStore(GROUND_TRUTH)) if os.path.exists(GROUND_TRUTH) else []


def test_there_is_ground_truth_to_check():
    """Skipped rather than failed when the owner has no such setup saved: a red suite that is red
    for a known, harmless reason teaches you to ignore red."""
    if not SETUPS:
        pytest.skip("no owner setup with a resistance line and a bull-flag box")


@pytest.mark.parametrize("setup", SETUPS, ids=lambda s: s["name"])
def test_detector_finds_the_owner_setup(setup):
    res = evaluate_setup(load_daily(), setup)
    assert res["found"], res
