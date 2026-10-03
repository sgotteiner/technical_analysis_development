"""
The owner's verdicts on the lines the CODE drew (2026-10-03: "if you want me to see and judge
tell me"), with his note and the line he would draw instead.

A verdict is about a line - a price, at a date - not about the settings that produced it, so a
later search with other settings is scored against it too. Judging the same line twice replaces
the old verdict: changing his mind must leave one truth, not two.
"""
from typing import Dict, List
from repositories.json_doc import JsonDoc, stamp
from schemas.sr_ground_truth_schema import JudgementIn, JudgementPatch

SECTION = "judgements"
SAME_LINE_PCT = 0.5        # re-judging the same line at the same date replaces the old verdict


def _same_line(a: Dict, b: Dict) -> bool:
    """One line judged twice: same chart, same "now", same kind, and within SAME_LINE_PCT. Prices
    move a little with the settings, so an exact match would pile up near-duplicate verdicts."""
    return (a["chart"] == b["chart"] and a["at"] == b["at"] and a["kind"] == b["kind"]
            and abs(a["price"] / b["price"] - 1) * 100 <= SAME_LINE_PCT)


class VerdictStore:
    def __init__(self, doc: JsonDoc):
        self.doc = doc

    def list_judgements(self) -> List[Dict]:
        return self.doc.items(SECTION)

    def judge(self, raw: Dict) -> Dict:
        item = {**stamp(), **JudgementIn(**raw).model_dump()}        # ValueError when invalid
        data = self.doc.read()
        data[SECTION] = [j for j in data[SECTION] if not _same_line(j, item)] + [item]
        self.doc.write(data)
        return item

    def annotate_judgement(self, judgement_id: str, raw: Dict) -> Dict:
        """The note on a verdict, and the drawing he put in its place."""
        patch = JudgementPatch(**raw).model_dump(exclude_unset=True)
        known = {a["id"] for a in self.doc.items("annotations")}
        if patch.get("replacement") and patch["replacement"] not in known:
            raise ValueError(f"unknown drawing: {patch['replacement']}")
        return self.doc.patch(SECTION, judgement_id, patch)

    def unjudge(self, judgement_id: str) -> bool:
        return self.doc.remove(SECTION, judgement_id)
