"""
What the system actually relies on, per drawing (owner, 2026-10-04: "i would like to revisit my
drawings easily so i could see the ground truth the system relies on").

The page must not answer this itself. Whether a drawing is read is decided by the code that reads
it - `ground_truth_score` takes lines and skips everything else, and the setup detector reads the
one resistance line and the one flag box of a qualifying setup - so this module asks THOSE, and the
panel only prints the answer. A second opinion in JavaScript is how the sidebar once showed
different numbers from the chart ("what is this joke").

A drawing with no reader is not waste: a sketch EXPLAINS, and that is its job. It is told apart
here so he can see at a glance which of his drawings are scoring the algorithm and which are
talking to Claude.
"""
from typing import Dict, List
from business_logic_services.ground_truth_score import SCORED_KIND
from business_logic_services.setup_evaluation import detector_members

# each reader gets a short badge and the sentence behind it, so the page can show one and explain
# with the other without inventing words of its own
SCORED, SCORED_WHY = "scored", "scored against the lines the code draws"
DETECTOR, DETECTOR_WHY = "setup detector", "read by the setup detector"
EXPLAINS, EXPLAINS_WHY = "explains only", "explains only - nothing scores it"
WHY = {SCORED: SCORED_WHY, DETECTOR: DETECTOR_WHY, EXPLAINS: EXPLAINS_WHY}


def usage(drawings: List[Dict], setups: List[Dict]) -> Dict[str, Dict]:
    """id -> {uses: [...], why: [...], setup: id|None, setup_name: str|None}. `setups` are the
    groups with their members resolved (SetupStore.setups_with_members)."""
    read_by_detector, in_setup = set(), {}
    for s in setups:
        members = detector_members(s)
        if members:
            read_by_detector.update(d["id"] for d in members.values())
        for d in s["drawings"]:
            in_setup[d["id"]] = s
    out: Dict[str, Dict] = {}
    for d in drawings:
        uses = []
        if d.get("kind") == SCORED_KIND:
            uses.append(SCORED)
        if d["id"] in read_by_detector:
            uses.append(DETECTOR)
        s = in_setup.get(d["id"])
        uses = uses or [EXPLAINS]
        out[d["id"]] = {"uses": uses, "why": [WHY[u] for u in uses], "scored": uses != [EXPLAINS],
                        "setup": s["id"] if s else None, "setup_name": s["name"] if s else None}
    return out
