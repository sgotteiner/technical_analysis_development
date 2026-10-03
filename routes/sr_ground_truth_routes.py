"""
The owner's ground truth: his drawings, his verdicts on the lines the code drew, and the score of
the code against both.

Separate from routes/sr_view_routes.py on purpose - these routes WRITE what the algorithm is
judged against, and nothing here computes a line.
"""
from typing import Dict
import pandas as pd
from fastapi import APIRouter, HTTPException
from business_logic_services.ground_truth_score import score_against_drawings
from business_logic_services.zone_service import zone_view
from repositories.sr_drawings_repo import DrawingStore
from repositories.sr_verdicts_repo import VerdictStore
from schemas.sr_view_schema import ZonesRequest


def make_ground_truth_router(df: pd.DataFrame, drawings: DrawingStore,
                             verdicts: VerdictStore, chart: str = "btc_1d") -> APIRouter:
    router = APIRouter(prefix="/api", tags=["S/R Ground Truth"])
    cache: Dict = {}

    @router.post("/score")
    def post_score(req: ZonesRequest):
        """What the code finds against what the owner drew, on the day he drew it."""
        if req.end >= len(df):
            raise HTTPException(422, f"end must be < {len(df)}")
        zones = zone_view(df, req.end, req.size, req.band_pct, req.min_visits, req.n_each, cache)
        lines = [a for a in drawings.list() if a["kind"] == "line"]
        trends = [{"at_now": float(t["at_now"]), "slope_pct_day": float(t["slope_pct_day"])}
                  for t in req.trends or []]
        return score_against_drawings(lines, {"zones": zones["zones"], "trends": trends},
                                      zones["price_now"], req.tol_pct or 3.0)

    @router.get("/judgements")
    def list_judgements():
        return verdicts.list_judgements()

    @router.post("/judgements")
    def add_judgement(raw: Dict):
        try:
            return verdicts.judge({"chart": chart, **raw})
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.patch("/judgements/{judgement_id}")
    def patch_judgement(judgement_id: str, raw: Dict):
        try:
            return verdicts.annotate_judgement(judgement_id, raw)
        except KeyError:
            raise HTTPException(404, "no such judgement")
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/judgements/{judgement_id}")
    def delete_judgement(judgement_id: str):
        if not verdicts.unjudge(judgement_id):
            raise HTTPException(404, "no such judgement")
        return {"deleted": judgement_id}

    @router.get("/annotations")
    def list_annotations():
        return drawings.list()

    @router.post("/annotations")
    def add_annotation(raw: Dict):
        try:
            return drawings.add({"chart": chart, **raw})
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.post("/annotations/group")
    def add_annotation_group(raw: Dict):
        """Several strokes that explain one thing, saved together with one note."""
        try:
            return drawings.add_many([{"chart": chart, **a} for a in raw.get("items", [])])
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/annotations/asked")
    def clear_asked():
        return {"deleted": drawings.clear_asked()}

    @router.patch("/annotations/{ann_id}")
    def patch_annotation(ann_id: str, raw: Dict):
        try:
            return drawings.update(ann_id, raw)
        except KeyError:
            raise HTTPException(404, "no such annotation")
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/annotations/{ann_id}")
    def delete_annotation(ann_id: str):
        if not drawings.delete(ann_id):
            raise HTTPException(404, "no such annotation")
        return {"deleted": ann_id}

    return router
