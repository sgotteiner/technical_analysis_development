"""
Ground-truth store for the S/R playground: the owner's own lines and pattern boxes, and setups
(groups of drawings with a note on how to trade them), kept in one JSON file so the shape blocks
and setup detectors can be tested against them. Writes are atomic (temp file + replace), so a
crash never leaves a half-written file.
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List
from schemas.sr_playground_schema import AnnotationIn, AnnotationPatch, SetupIn, SetupPatch


def _stamp() -> Dict:
    return {"id": uuid.uuid4().hex[:12], "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}


class AnnotationStore:
    def __init__(self, path):
        self.path = Path(path)

    def _read(self) -> Dict:
        if not self.path.exists():
            return {"annotations": [], "setups": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        data.setdefault("setups", [])
        return data

    def _write(self, data: Dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    # ---- drawings ----
    def list(self) -> List[Dict]:
        return self._read()["annotations"]

    def add(self, raw: Dict) -> Dict:
        ann = {**_stamp(), **AnnotationIn(**raw).model_dump()}         # ValueError when invalid
        data = self._read()
        data["annotations"].append(ann)
        self._write(data)
        return ann

    def update(self, ann_id: str, raw: Dict) -> Dict:
        return self._patch("annotations", ann_id, AnnotationPatch(**raw).model_dump(exclude_none=True))

    def delete(self, ann_id: str) -> bool:
        data = self._read()
        kept = [a for a in data["annotations"] if a["id"] != ann_id]
        if len(kept) == len(data["annotations"]):
            return False
        data["annotations"] = kept
        for s in data["setups"]:
            s["members"] = [m for m in s["members"] if m != ann_id]
        self._write(data)
        return True

    # ---- setups ----
    def list_setups(self) -> List[Dict]:
        return self._read()["setups"]

    def add_setup(self, raw: Dict) -> Dict:
        setup = {**_stamp(), **SetupIn(**raw).model_dump()}
        data = self._read()
        self._check_members(data, setup["members"])
        data["setups"].append(setup)
        self._write(data)
        return setup

    def update_setup(self, setup_id: str, raw: Dict) -> Dict:
        patch = SetupPatch(**raw).model_dump(exclude_none=True)
        if "members" in patch:
            self._check_members(self._read(), patch["members"])
        return self._patch("setups", setup_id, patch)

    def delete_setup(self, setup_id: str) -> bool:
        data = self._read()
        kept = [s for s in data["setups"] if s["id"] != setup_id]
        if len(kept) == len(data["setups"]):
            return False
        data["setups"] = kept
        self._write(data)
        return True

    def setups_with_members(self) -> List[Dict]:
        by_id = {a["id"]: a for a in self.list()}
        return [{**s, "drawings": [by_id[m] for m in s["members"]]} for s in self.list_setups()]

    # ---- helpers ----
    def _patch(self, section: str, item_id: str, patch: Dict) -> Dict:
        data = self._read()
        for item in data[section]:
            if item["id"] == item_id:
                item.update(patch)
                self._write(data)
                return item
        raise KeyError(item_id)

    @staticmethod
    def _check_members(data: Dict, members: List[str]) -> None:
        missing = set(members) - {a["id"] for a in data["annotations"]}
        if missing:
            raise ValueError(f"unknown drawings: {sorted(missing)}")
