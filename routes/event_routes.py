"""
/api/events: the events up to "now", each with the line it happened at and why - plus the date of
every event in history, so the page can step from one to the next (owner, 2026-10-08: "in contrast
to lines events are not every candle so thats a question how i would see them").
"""
import pandas as pd
from fastapi import APIRouter, HTTPException
from business_logic_services.event_service import EventFlags, compute_events
from business_logic_services.line_modes import concepts_of
from business_logic_services.trade_view import trades_view
from schemas.event_schema import EventSwitches, EventsRequest
from schemas.sr_view_schema import ConceptFlags


def flags_of(req: EventsRequest):
    cf, ef = req.concepts or ConceptFlags(), req.events or EventSwitches()
    c = concepts_of(cf)
    f = EventFlags(**{**ef.model_dump(), "types": tuple(ef.types), "patterns": tuple(ef.patterns)})
    return c, f


def make_event_router(df: pd.DataFrame, cache: dict = None) -> APIRouter:
    router = APIRouter(prefix="/api")
    cache = cache if cache is not None else {}     # the page's: the zigzag of each day is computed once

    @router.post("/events")
    def post_events(req: EventsRequest):
        if req.end >= len(df):
            raise HTTPException(422, f"end {req.end} is past the last bar")
        c, f = flags_of(req)
        events = compute_events(df, c, req.size, f, cache)
        print(f"EVENTS {df.index[req.end].date()} | {len(events)} in history | types {'+'.join(f.types)}"
              f" | patterns {'+'.join(f.patterns) or '-'} | closes {f.closes} | candle {f.candle}", flush=True)
        # the card shows what is known at "now"; the steps are only where the arrows can jump to
        return {"end": req.end, "events": [e for e in events if e["bar"] <= req.end],
                "steps": sorted({e["bar"] for e in events})}

    @router.get("/trades")
    def get_trades(end: int, lines: str = "zigzag"):
        """His breakout -> retest strategy's trades opened by `end` (an exit after `end` is not shown)."""
        if lines not in ("zigzag",):
            raise HTTPException(422, "trades are run on the kept zigzag lines only")
        res = trades_view(df, lines, cache)
        shown = [t if t["exit_bar"] <= end else {**t, "exit_bar": None, "exit_time": None, "exit": None,
                                                  "how": "open", "result": "Still open on this date."}
                 for t in res["trades"] if t["entry_bar"] <= end]
        s, still = res["stats"], sum(t["how"] == "open" for t in shown)
        print(f"TRADES {df.index[end].date()} | {len(shown)} up to now ({still} open) | whole history: {s.get('trades', 0)} "
              f"trades, win {s.get('win_rate', 0):.0f}%, PF {s.get('profit_factor', 0):.2f}, compounded "
              f"{s.get('compounded', 0):+.0f}%", flush=True)
        return {"end": end, "trades": shown, "stats": s}

    @router.post("/seen")
    def post_seen(what: dict):
        """What he opened on the chart - a line, a trade, an event or a star - so the log says what he is
        looking at without him pasting it (owner, 2026-10-09)."""
        print(f"CARD {str(what.get('head', ''))[:80]} | {str(what.get('first', ''))[:160]}", flush=True)
        return {"ok": True}

    return router
