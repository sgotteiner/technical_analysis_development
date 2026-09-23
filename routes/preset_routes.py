"""
Preset API: the saved playground states (config/sr_presets.yaml) — settings plus the commit they
were produced on, so a state can be brought back together with its code.
"""
from typing import Dict
from fastapi import APIRouter, HTTPException
from repositories.sr_preset_repo import PresetStore


def make_preset_router(store: PresetStore) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["Presets"])

    @router.get("/presets")
    def list_presets():
        return store.list()

    @router.post("/presets")
    def save_preset(body: Dict):
        try:
            return store.save(body.get("name", ""), body.get("settings") or {}, body.get("note", ""))
        except ValueError as e:
            raise HTTPException(422, str(e))

    return router
