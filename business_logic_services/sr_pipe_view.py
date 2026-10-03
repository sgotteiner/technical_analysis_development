"""
The pipe view (owner, 2026-09-22): change the S/R settings and see the lines at once - per level,
the ranked pipes, the ranked single lines, and the swing legs the width rules are judged against.

This is the first thing the playground did, and it is independent of the setup layer that came
later: nothing here knows about levels, moves or the story. Only candles up to `end` are used (the
shape blocks guarantee it).
"""
from typing import Dict, Optional
import numpy as np
import pandas as pd
from business_logic_services.swing_frame import turning_points_cached
from modules.shapes.sr_lines import candidate_lines, top_lines
from modules.shapes.sr_pipes import ranked_pipes, swing_legs, pipe_width
from modules.shapes.sr_settings import SRRules

MAX_PAIRS = 50_000_000      # pipe-search budget per level; beyond it the view says "incomplete"


def _level_view(df, end, cfg, rules, pairs, singles, tp) -> Dict:
    m, period = cfg["magnitude"], cfg["period"]
    tp_cand, tp_full = tp(m * rules.candidate_ratio), tp(m)
    lines = candidate_lines(df, end, period, m, tp_cand, rules)
    info = {}
    pipes = ranked_pipes(df, end, period, m, pairs, tp_cand, tp_full, rules, MAX_PAIRS, info, lines) if pairs else []
    legs = swing_legs(df, end, period, m, tp_full)
    return {"pipes": [{"support": lo, "resistance": up, "width": pipe_width(lo, up)} for lo, up in pipes],
            "lines": top_lines(lines, singles) if singles else [],
            "candidates": len(lines), "complete": bool(info.get("complete", True)),
            "checked_down_to": info.get("checked_down_to"),
            "largest_swing": float(legs.max()) if len(legs) else None,
            "median_swing": float(np.median(legs)) if len(legs) else None}


def playground_view(df: pd.DataFrame, end: int, levels: Dict, rules: SRRules, pairs: int = 1,
                    singles: int = 0, cache: Optional[Dict] = None) -> Dict:
    """`cache` may hold turning points of the WHOLE df per threshold; only points confirmed by
    `end` are ever used, so it is safe to share between calls with different `end`."""
    shared = cache if cache is not None else {}       # one dict for the whole view, not per level
    tp = lambda th: turning_points_cached(df, th, shared)
    return {"end": int(end),
            "levels": {name: _level_view(df, end, cfg, rules, pairs, singles, tp)
                       for name, cfg in levels.items()}}
