"""
The lines the S/R algorithm draws at a date - THE one source of lines. The page draws them, and the
events and strategies read the very same lines (owner, 2026-10-08: "if i said i care about a line in
the sr algorithm i want to see the breakout of this line. not a breakout for an invented line").

Moved here from routes/sr_view_routes.py unchanged, so the page and the history can share it.
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from business_logic_services.frozen_zigzag import frozen_points, frozen_swing_points
from business_logic_services.level_strength import add_strength
from business_logic_services.line_modes import mode_lines
from business_logic_services.line_rules import point_lines
from business_logic_services.setup_view import story_view
from business_logic_services.swing_frame import swing_frame
from business_logic_services.swing_view import swing_points
from business_logic_services.trend_structure import read_structure, zigzag
from schemas.sr_view_schema import ConceptFlags


def trend_at_now(trends: list, end: int) -> Optional[Dict]:
    """The first trend line as the story needs it: where it stands today, and how fast it rises."""
    tr = (trends or [None])[0]
    if not tr:
        return None
    return {"at_now": float(np.exp(tr["y1"] + tr["slope"] * (end - tr["x1"]))),
            "slope_pct_day": float(np.expm1(tr["slope"]) * 100),
            "first": tr["first"], "last": tr["last"], "touches": tr["touches"],
            "direction": tr.get("direction"), "previous": bool(tr.get("previous")),
            "far": bool(tr.get("far")), "away_pct": tr.get("away_pct"),
            "points": tr.get("points", []),
            "peaks": tr.get("peaks", []), "valleys": tr.get("valleys", [])}


def screen_lines(df: pd.DataFrame, end: int, s: float, cfg, pts: list, cache: Dict) -> Dict:
    """Levels, trends, zigzag and the setup card (`story`) for rule `cfg.mode` at `end`. Raises
    ValueError when the settings cannot be computed."""
    other = mode_lines(df, end, cfg.mode, cfg.concepts or ConceptFlags(), s, cache)
    if other is not None:
        return other
    out: Dict = {}
    close = df["Close"].to_numpy()
    big = swing_points(df, end, round(s * cfg.target_scale, 4), cache)
    # the trend and the level width are read against the structure price is in
    # (structure_scale), not against every wiggle of the dots
    owner = cfg.mode == "owner"
    trend, yard = read_structure(df, end, pts[-1]["running_move"] if pts else 0.0, s, cache) if owner else (None, 0.0)
    frozen = frozen_points(df, end, s, cache) if owner else None
    out["zigzag"] = zigzag(df, end, trend["size"] if trend else s, cache, frozen)
    frame = swing_frame(df, end, s, cache)
    # support and resistance from the same zigzag the trend is read from - the peaks and valleys at
    # the move's scale, not every 7% wiggle (owner, 2026-10-07: "i want the support and resistance
    # to also use that")
    level_pts = ([{**p, "running_move": pts[-1]["running_move"]} for p in frozen_swing_points(df, end, s, cache)]
                 if owner and trend and pts else pts)
    out.update(point_lines(level_pts, cfg, end, float(close[end]), float(close[max(0, end - 10)]), big, size=s,
                           trend=trend, yardstick=yard, turned_at=frame.turned_at(),
                           move_from_bar=frame.now_from_bar if owner else 0.0))
    if owner and trend and out.get("levels"):
        out["levels"] = add_strength(out["levels"], frozen, df["High"].to_numpy(), df["Low"].to_numpy(), end, yard)
    out["story"] = story_view(df, end, s, out.get("levels") or [], trend_at_now(out.get("trends"), end),
                              cfg.band_pct or s * 100 / 2, cache, touch_pct=cfg.tol_pct or 1.4)
    return out
