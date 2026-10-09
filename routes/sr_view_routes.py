"""
What the playground DRAWS: candles, the default settings, and the view for any "now" + settings.

Read-only - nothing here touches the owner's ground truth (routes/sr_ground_truth_routes.py).
A route's job is to validate the request and hand it to a service; the shaping of an answer
belongs in the service, not here.
"""
from typing import Dict, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException
from business_logic_services.setup_view import picture_start
from business_logic_services.sr_pipe_view import playground_view
from business_logic_services.swing_view import swing_box_view, swing_points
from business_logic_services.swing_frame import turning_points_cached
from business_logic_services.zone_service import zone_view
from modules.shapes.sr_settings import DEFAULT_LEVELS, DEFAULT_RULES, parse_rules
from modules.shapes.swing_calibration import calibrate_size
from modules.shapes.sr_turning_points import PEAK, turning_points
from business_logic_services.line_modes import flags_text
from business_logic_services.screen_lines import screen_lines
from business_logic_services.line_events import line_events
from schemas.sr_view_schema import ConceptFlags, PointsRequest, ViewRequest, ZonesRequest
from schemas.sr_ground_truth_schema import LABELS



def close_points(df: pd.DataFrame, end: int, size: float) -> list:
    """The same zigzag with its swings measured on CLOSES, to see beside the high/low dots - which
    turning points the closes keep and which only a wick made (owner, 2026-10-07: "can i see this
    closure dots idea on the graph?"). Shown only; nothing is computed from them."""
    tp = turning_points(df, size, on_closes=True)
    known = (tp["conf"] <= end) & (tp["idx"] <= end)
    return [{"time": int(df.index[int(i)].timestamp()), "kind": "peak" if k == PEAK else "valley"}
            for i, k in zip(tp["idx"][known], tp["kind"][known])]


def make_view_router(df: pd.DataFrame, chart: str = "btc_1d", cache: Optional[Dict] = None) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["S/R Playground"])
    candles = [{"time": int(t.timestamp()), "open": float(o), "high": float(h), "low": float(l), "close": float(c)}
               for t, o, h, l, c in zip(df.index, df["Open"], df["High"], df["Low"], df["Close"])]
    cache = cache if cache is not None else {}   # turning points of the whole df, per threshold - shared with the events

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
        # say WHERE he is looking, in the server log. Everything he reports is about the date on
        # his screen, and without this the only dates anyone can check are the ones Claude picks
        # (owner, 2026-10-05: "you dont check what i say based on the date im at?").
        ln = req.lines
        print(f"VIEW {df.index[req.end].date()} (bar {req.end})"
              f" | sizes {[round(s * 100, 1) for s in req.sizes] or 'calibrated'}"
              f" | band {getattr(ln, 'merge_pct', None)} | visits {getattr(ln, 'min_visits', None)}"
              f" | mode {getattr(ln, 'mode', None)}"
              + (f" [{flags_text(ln.concepts or ConceptFlags())}]" if ln is not None and ln.mode == "concepts" else "")
              + f" | on: {' '.join(k for k, v in (req.layers or {}).items() if v) or '?'}", flush=True)
        calibrated = calibrate_size(df, req.end, req.target_days) if req.target_days else None
        sizes = list(req.sizes)
        if calibrated and calibrated["size"] and not sizes:
            sizes = [round(calibrated["size"], 4)]
        groups = []
        for s in sizes:
            band = (req.lines.band_pct if req.lines else None) or s * 100 / 2
            start = picture_start(df, req.end, s, band, cache)
            pts = swing_points(df, req.end, s, cache, req.lookback_days)
            # Only the boxes that belong to the LINES the code drew - owner, 2026-10-05: "i want
            # only the related boxes to the calculated lines. now i see a million boxes." Drawing
            # one box per turning point put 1,012 on the chart at 7%.
            group = {"size": s, "points": pts, "boxes": [], "close_points": close_points(df, req.end, s),
                     "picture_from": int(df.index[int(start)].timestamp())}
            if req.lines:
                try:
                    group.update(screen_lines(df, req.end, s, req.lines, pts, cache))
                except ValueError as e:
                    raise HTTPException(422, str(e))
            if group.get("story"):          # the stars: what happened at these lines in the move now
                group["line_events"] = line_events(df, req.end, group["story"], req.lines.tol_pct)
            groups.append(group)
        return {"end": req.end, "calibrated": calibrated, "sizes": groups}

    @router.post("/zones")
    def post_zones(req: ZonesRequest):
        within(req.end)
        return zone_view(df, req.end, req.size, req.band_pct, req.min_visits, req.n_each, cache)

    return router
