"""
S/R playground API: candles, default settings, the live view for any "now" + settings, and the
owner's ground-truth drawings (CRUD). Built per app so tests can pass their own data and file.
"""
from typing import Dict
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from modules.shapes.sr_settings import DEFAULT_LEVELS, DEFAULT_RULES, parse_rules
from repositories.sr_annotation_repo import AnnotationStore
from modules.shapes.swing_calibration import calibrate_size
from business_logic_services.sr_playground_service import (playground_view, swing_points,
                                                           point_lines, swing_box_view,
                                                           story_view, picture_start)
from business_logic_services.zone_service import zone_view
from business_logic_services.ground_truth_score import score_against_drawings
from schemas.sr_playground_schema import PointsRequest, ViewRequest, ZonesRequest, LABELS


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
        from scripts.sr_playground import ui_build
        return {"levels": DEFAULT_LEVELS, "rules": DEFAULT_RULES.as_dict(), "chart": chart,
                "labels": LABELS, "build": ui_build()}

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
            band = (req.lines.band_pct if req.lines else None) or s * 100 / 2
            start = picture_start(df, req.end, s, band, cache)
            group = {"size": s, "points": pts,
                     "boxes": swing_box_view(df, req.end, s, cache, start),
                     "picture_from": int(df.index[int(start)].timestamp())}
            if req.lines:
                try:
                    close = df["Close"].to_numpy()
                    big = swing_points(df, req.end, round(s * req.lines.target_scale, 4), cache)
                    group.update(point_lines(pts, req.lines, req.end, float(close[req.end]),
                                             float(close[max(0, req.end - 10)]), big, size=s))
                    tr = (group.get("trends") or [None])[0]
                    now = req.end
                    trend = None if not tr else {
                        "at_now": float(np.exp(tr["y1"] + tr["slope"] * (now - tr["x1"]))),
                        "slope_pct_day": float(np.expm1(tr["slope"]) * 100),
                        "first": tr["first"], "last": tr["last"], "touches": tr["touches"],
                        "points": tr.get("points", [])}
                    group["story"] = story_view(df, req.end, s, group.get("levels") or [],
                                                trend, req.lines.band_pct or s * 100 / 2,
                                                cache)
                except ValueError as e:
                    raise HTTPException(422, str(e))
            groups.append(group)
        return {"end": req.end, "calibrated": calibrated, "sizes": groups}

    @router.post("/zones")
    def post_zones(req: ZonesRequest):
        if req.end >= len(df):
            raise HTTPException(422, f"end must be < {len(df)}")
        return zone_view(df, req.end, req.size, req.band_pct, req.min_visits, req.n_each, cache)

    @router.post("/score")
    def post_score(req: ZonesRequest):
        """What the code finds against what the owner drew, on the day he drew it."""
        if req.end >= len(df):
            raise HTTPException(422, f"end must be < {len(df)}")
        zones = zone_view(df, req.end, req.size, req.band_pct, req.min_visits, req.n_each, cache)
        drawings = [a for a in store.list() if a["kind"] == "line"]
        trends = [{"at_now": float(t["at_now"]), "slope_pct_day": float(t["slope_pct_day"])}
                  for t in req.trends or []]
        return score_against_drawings(drawings, {"zones": zones["zones"], "trends": trends},
                                      zones["price_now"], req.tol_pct or 3.0)

    @router.get("/judgements")
    def list_judgements():
        return store.list_judgements()

    @router.post("/judgements")
    def add_judgement(raw: Dict):
        try:
            return store.judge({"chart": chart, **raw})
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.patch("/judgements/{judgement_id}")
    def patch_judgement(judgement_id: str, raw: Dict):
        try:
            return store.annotate_judgement(judgement_id, raw)
        except KeyError:
            raise HTTPException(404, "no such judgement")
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/judgements/{judgement_id}")
    def delete_judgement(judgement_id: str):
        if not store.unjudge(judgement_id):
            raise HTTPException(404, "no such judgement")
        return {"deleted": judgement_id}

    @router.get("/annotations")
    def list_annotations():
        return store.list()

    @router.post("/annotations")
    def add_annotation(raw: Dict):
        try:
            return store.add({"chart": chart, **raw})
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.post("/annotations/group")
    def add_annotation_group(raw: Dict):
        """Several strokes that explain one thing, saved together with one note."""
        try:
            return store.add_many([{"chart": chart, **a} for a in raw.get("items", [])])
        except ValueError as e:
            raise HTTPException(422, str(e))

    @router.delete("/annotations/asked")
    def clear_asked():
        return {"deleted": store.clear_asked()}

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
