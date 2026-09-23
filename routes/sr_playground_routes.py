"""
S/R playground API: candles, default settings, the live view for any "now" + settings, and the
owner's ground-truth drawings (CRUD). Built per app so tests can pass their own data and file.
"""
from typing import Dict
import pandas as pd
from fastapi import APIRouter, HTTPException
from modules.shapes.sr_settings import DEFAULT_LEVELS, DEFAULT_RULES, parse_rules
from repositories.sr_annotation_repo import AnnotationStore
from modules.shapes.swing_calibration import calibrate_size
from business_logic_services.sr_playground_service import playground_view, swing_points, point_lines
from schemas.sr_playground_schema import PointsRequest, ViewRequest, LABELS


def make_router(df: pd.DataFrame, store: AnnotationStore, chart: str = "btc_1d") -> APIRouter:
    router = APIRouter(prefix="/api", tags=["S/R Playground"])
    candles = [{"time": int(t.timestamp()), "open": float(o), "high": float(h), "low": float(l), "close": float(c)}
               for t, o, h, l, c in zip(df.index, df["Open"], df["High"], df["Low"], df["Close"])]
    cache: Dict = {}                          # turning points of the whole df, per threshold

    @router.get("/candles")
    def get_candles():
        return candles

    @router.get("/defaults")
    def get_defaults():
        return {"levels": DEFAULT_LEVELS, "rules": DEFAULT_RULES.as_dict(), "chart": chart, "labels": LABELS}

    @router.post("/view")
    def post_view(req: ViewRequest):
        if req.end >= len(df):
            raise HTTPException(422, f"end must be < {len(df)}")
        return playground_view(df, req.end, req.levels, parse_rules(req.rules), req.pairs, req.singles, cache)

    @router.post("/points")
    def post_points(req: PointsRequest):
        if req.end >= len(df):
            raise HTTPException(422, f"end must be < {len(df)}")
        calibrated = calibrate_size(df, req.end, req.target_days) if req.target_days else None
        sizes = list(req.sizes)
        if calibrated and calibrated["size"] and not sizes:
            sizes = [round(calibrated["size"], 4)]
        groups = []
        for s in sizes:
            pts = swing_points(df, req.end, s, cache, req.lookback_days)
            group = {"size": s, "points": pts}
            if req.lines:
                try:
                    group.update(point_lines(pts, req.lines, req.end))
                except ValueError as e:
                    raise HTTPException(422, str(e))
            groups.append(group)
        return {"end": req.end, "calibrated": calibrated, "sizes": groups}

    @router.get("/annotations")
    def list_annotations():
        return store.list()

    @router.post("/annotations")
    def add_annotation(raw: Dict):
        try:
            return store.add({"chart": chart, **raw})
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.patch("/annotations/{ann_id}")
    def patch_annotation(ann_id: str, raw: Dict):
        try:
            return store.update(ann_id, raw)
        except KeyError:
            raise HTTPException(404, "no such annotation")
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/annotations/{ann_id}")
    def delete_annotation(ann_id: str):
        if not store.delete(ann_id):
            raise HTTPException(404, "no such annotation")
        return {"deleted": ann_id}

    return router
