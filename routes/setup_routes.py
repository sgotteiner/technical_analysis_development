"""
Setup API: the owner's setup groups (CRUD), the detector's episodes over the whole chart (computed
once, on first request), and how each drawn setup fares against the detector.
"""
from typing import Dict
import pandas as pd
from fastapi import APIRouter, HTTPException
from business_logic_services.setup_evaluation import detection_episodes, evaluate_setup, resistance_flag_setups
from repositories.sr_annotation_repo import AnnotationStore


def make_setup_router(df: pd.DataFrame, store: AnnotationStore) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["Setups"])
    cache: Dict = {}

    @router.get("/setups")
    def list_setups():
        return store.list_setups()

    @router.post("/setups")
    def add_setup(raw: Dict):
        try:
            return store.add_setup(raw)
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.patch("/setups/{setup_id}")
    def patch_setup(setup_id: str, raw: Dict):
        try:
            return store.update_setup(setup_id, raw)
        except KeyError:
            raise HTTPException(404, "no such setup")
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/setups/{setup_id}")
    def delete_setup(setup_id: str):
        if not store.delete_setup(setup_id):
            raise HTTPException(404, "no such setup")
        return {"deleted": setup_id}

    @router.get("/setups/evaluation")
    def evaluation():
        return {s["id"]: evaluate_setup(df, s) for s in resistance_flag_setups(store)}

    @router.get("/setup-detections")
    def detections():
        if "episodes" not in cache:
            cache["episodes"] = detection_episodes(df)
        return cache["episodes"]

    return router
