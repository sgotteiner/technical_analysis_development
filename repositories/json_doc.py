"""
One JSON file, with sections, written atomically.

The ground truth is three collections - the owner's drawings, his setups and his verdicts - and
they live in one file so that deleting a drawing can also tidy the setups and verdicts that point
at it in a single write. That is a storage concern, so it lives here on its own, and each
collection gets its own store over it (repositories/sr_drawings_repo.py and friends).
"""
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

SECTIONS = ("annotations", "setups", "judgements")


def stamp() -> Dict:
    """What every record gets on the way in: an id and when it was made."""
    return {"id": uuid.uuid4().hex[:12],
            "created": datetime.now(timezone.utc).isoformat(timespec="seconds")}


class JsonDoc:
    """The file. A store asks it for the whole document, changes it, and hands it back."""

    def __init__(self, path):
        self.path = Path(path)

    def read(self) -> Dict:
        if not self.path.exists():
            return {s: [] for s in SECTIONS}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        for s in SECTIONS:
            data.setdefault(s, [])
        return data

    def write(self, data: Dict) -> None:
        """Temp file + replace, so a crash never leaves a half-written answer key."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, self.path)

    def items(self, section: str) -> List[Dict]:
        return self.read()[section]

    def append(self, section: str, items: List[Dict]) -> List[Dict]:
        data = self.read()
        data[section].extend(items)
        self.write(data)
        return items

    def patch(self, section: str, item_id: str, patch: Dict) -> Dict:
        data = self.read()
        for item in data[section]:
            if item["id"] == item_id:
                item.update(patch)
                self.write(data)
                return item
        raise KeyError(item_id)

    def remove(self, section: str, item_id: str) -> bool:
        data = self.read()
        kept = [i for i in data[section] if i["id"] != item_id]
        if len(kept) == len(data[section]):
            return False
        data[section] = kept
        self.write(data)
        return True
