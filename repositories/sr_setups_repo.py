"""
Setups: several of the owner's drawings that belong together, and how he would trade them.

A setup only ever holds drawings that exist - checked on the way in, because a setup pointing at a
drawing that was deleted is a hole in the answer key, not a harmless dangling id.
"""
from typing import Dict, List
from repositories.json_doc import JsonDoc, stamp
from schemas.sr_ground_truth_schema import SetupIn, SetupPatch

SECTION = "setups"


class SetupStore:
    def __init__(self, doc: JsonDoc):
        self.doc = doc

    def list_setups(self) -> List[Dict]:
        return self.doc.items(SECTION)

    def add_setup(self, raw: Dict) -> Dict:
        setup = {**stamp(), **SetupIn(**raw).model_dump()}
        self._check_members(setup["members"])
        return self.doc.append(SECTION, [setup])[0]

    def update_setup(self, setup_id: str, raw: Dict) -> Dict:
        patch = SetupPatch(**raw).model_dump(exclude_none=True)
        if "members" in patch:
            self._check_members(patch["members"])
        return self.doc.patch(SECTION, setup_id, patch)

    def delete_setup(self, setup_id: str) -> bool:
        return self.doc.remove(SECTION, setup_id)

    def setups_with_members(self) -> List[Dict]:
        """Each setup with its drawings in hand, which is how a detector is scored against it."""
        data = self.doc.read()
        by_id = {a["id"]: a for a in data["annotations"]}
        return [{**s, "drawings": [by_id[m] for m in s["members"] if m in by_id]}
                for s in data[SECTION]]

    def _check_members(self, members: List[str]) -> None:
        missing = set(members) - {a["id"] for a in self.doc.items("annotations")}
        if missing:
            raise ValueError(f"unknown drawings: {sorted(missing)}")
