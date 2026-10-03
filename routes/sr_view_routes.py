"""
What the playground DRAWS: candles, the default settings, and the view for any "now" + settings.

Read-only - nothing here touches the owner's ground truth (routes/sr_ground_truth_routes.py).
A route's job is to validate the request and hand it to a service; the shaping of an answer
belongs in the service, not here.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from business_logic_services.line_rules import point_lines
from business_logic_services.setup_view import picture_start, story_view
from business_logic_services.sr_pipe_view import playground_view
from business_logic_services.swing_view import swing_box_view, swing_points
from business_logic_services.zone_service import zone_view
from modules.shapes.sr_settings import DEFAULT_LEVELS, DEFAULT_RULES, parse_rules
from modules.shapes.swing_calibration import calibrate_size
from schemas.sr_view_schema import PointsRequest, ViewRequest, ZonesRequest
from schemas.sr_ground_truth_schema import LABELS


def trend_at_now(trends: list, end: int) -> Optional[Dict]:
    """The first trend line as the story needs it: where it stands today, and how fast it rises."""
    tr = (trends or [None])[0]
    if not tr:
        return None
    return {"at_now": float(np.exp(tr["y1"] + tr["slope"] * (end - tr["x1"]))),
            "slope_pct_day": float(np.expm1(tr["slope"]) * 100),
            "first": tr["first"], "last": tr["last"], "touches": tr["touches"],
            "points": tr.get("points", [])}


def make_view_router(df: pd.DataFrame, chart: str = "btc_1d") -> APIRouter:
    router = APIRouter(prefix="/api", tags=["S/R Playground"])
    candles = [{"time": int(t.timestamp()), "open": float(o), "high": float(h), "low": float(l), "close": float(c)}
               for t, o, h, l, c in zip(df.index, df["Open"], df["High"], df["Low"], df["Close"])]
    cache: Dict = {}                          # turning points of the whole df, per threshold

    def within(end: int) -> None:
        if end >= len(df):
            raise HTTPException(422, f"end must be < {len(df)}")

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
        within(req.end)
        return playground_view(df, req.end, req.levels, parse_rules(req.rules), req.pairs, req.singles, cache)

    @router.post("/points")
    def post_points(req: PointsRequest):
        within(req.end)
        calibrated = calibrate_size(df, req.end, req.target_days) if req.target_days else None
        sizes = list(req.sizes)
        if calibrated and calibrated["size"] and not sizes:
            sizes = [round(calibrated["size"], 4)]
        groups = []
        for s in sizes:
            band = (req.lines.band_pct if req.lines else None) or s * 100 / 2
            start = picture_start(df, req.end, s, band, cache)
            pts = swing_points(df, req.end, s, cache, req.lookback_days)
            group = {"size": s, "points": pts,
                     "boxes": swing_box_view(df, req.end, s, cache, start),
                     "picture_from": int(df.index[int(start)].timestamp())}
            if req.lines:
                try:
                    close = df["Close"].to_numpy()
                    big = swing_points(df, req.end, round(s * req.lines.target_scale, 4), cache)
                    group.update(point_lines(pts, req.lines, req.end, float(close[req.end]),
                                             float(close[max(0, req.end - 10)]), big, size=s))
                    group["story"] = story_view(df, req.end, s, group.get("levels") or [],
                                                trend_at_now(group.get("trends"), req.end),
                                                req.lines.band_pct or s * 100 / 2, cache)
                except ValueError as e:
                    raise HTTPException(422, str(e))
            groups.append(group)
        return {"end": req.end, "calibrated": calibrated, "sizes": groups}

    @router.post("/zones")
    def post_zones(req: ZonesRequest):
        within(req.end)
        return zone_view(df, req.end, req.size, req.band_pct, req.min_visits, req.n_each, cache)

    return router
