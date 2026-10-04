"""
The owner's drawings: his lines, pattern boxes and sketches - the answer key the shape blocks and
setup detectors are tested against.

Deleting a drawing cascades: a setup must not list a member that is gone, and a verdict must not
point at a replacement that is gone. Both happen in the same write, which is why the three
collections share one document (repositories/json_doc.py).
"""
from typing import Dict, List
from repositories.json_doc import JsonDoc, stamp
from schemas.sr_ground_truth_schema import AnnotationIn, AnnotationPatch

SECTION = "annotations"


class DrawingStore:
    def __init__(self, doc: JsonDoc):
        self.doc = doc

    def list(self) -> List[Dict]:
        return self.doc.items(SECTION)

    def add(self, raw: Dict) -> Dict:
        ann = {**stamp(), **AnnotationIn(**raw).model_dump()}          # ValueError when invalid
        return self.doc.append(SECTION, [ann])[0]

    def add_many(self, raws: List[Dict]) -> List[Dict]:
        """One group of strokes explaining one thing: all or nothing, so a half-saved group never
        appears (owner, 2026-10-03: "id like to make more than one draw for a certain note")."""
        items = [{**stamp(), **AnnotationIn(**raw).model_dump()} for raw in raws]   # validate first
        return self.doc.append(SECTION, items)

    def update(self, ann_id: str, raw: Dict) -> Dict:
        """Label, note, or a new shape. A new shape is validated by the rule that accepted the
        drawing in the first place (AnnotationIn), against the kind it already has - so a box
        cannot be patched into something that is not a box."""
        patch = AnnotationPatch(**raw).model_dump(exclude_none=True)
        if "points" in patch:
            now = next((a for a in self.list() if a["id"] == ann_id), None)
            if now is None:
                raise KeyError(ann_id)
            AnnotationIn(**{**now, **patch})                           # ValueError when invalid
        return self.doc.patch(SECTION, ann_id, patch)

    def delete(self, ann_id: str) -> bool:
        return self._drop({ann_id}) == 1

    def delete_group(self, group: str) -> int:
        """All the strokes of one explanation, in one write: he drew it as one thing, so he
        removes it as one thing (owner, 2026-10-04: "read add remove edit easily")."""
        return self._drop({a["id"] for a in self.list() if a.get("group") == group})

    def clear_asked(self) -> int:
        """Drop the sketches he only drew to explain something. His own drawings are untouched."""
        return self._drop({a["id"] for a in self.list() if a.get("purpose") == "ask"})

    def _drop(self, ids: set) -> int:
        if not ids:
            return 0
        data = self.doc.read()
        kept = [a for a in data[SECTION] if a["id"] not in ids]
        if len(kept) == len(data[SECTION]):
            return 0
        data[SECTION] = kept
        for s in data["setups"]:
            s["members"] = [m for m in s["members"] if m not in ids]
        for j in data["judgements"]:
            if j.get("replacement") in ids:
                j["replacement"] = None   # the drawing is gone; the verdict and its note stay
        self.doc.write(data)
        return len(ids)
