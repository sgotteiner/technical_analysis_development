"""
The ground truth as one object, for tests only.

The app keeps the three stores apart on purpose - each router is handed just the collection it is
allowed to touch - but a test often exercises two of them over the same file, because the
collections really do interact: deleting a drawing has to tidy the setups and verdicts that point
at it. Composing them here keeps that wiring out of every test, and out of production.
"""
from repositories.json_doc import JsonDoc
from repositories.sr_drawings_repo import DrawingStore
from repositories.sr_setups_repo import SetupStore
from repositories.sr_verdicts_repo import VerdictStore


class GroundTruth(DrawingStore, SetupStore, VerdictStore):
    def __init__(self, path):
        super().__init__(JsonDoc(path))
