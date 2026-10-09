"""The events request: the lines' switches and the events' switches (business_logic_services/event_service.py)."""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field
from schemas.sr_view_schema import ConceptFlags

EventType = Literal["breakout", "fakeout", "sweep", "retest", "bounce", "trend_change"]
PatternType = Literal["double_top", "double_bottom", "head_shoulders", "inverse_head_shoulders",
                      "cup_handle", "bull_flag", "bear_flag"]


class EventSwitches(BaseModel):
    types: List[EventType] = ["breakout", "fakeout", "sweep", "retest", "bounce", "trend_change"]
    patterns: List[PatternType] = ["double_top", "double_bottom", "head_shoulders", "inverse_head_shoulders",
                                   "cup_handle", "bull_flag", "bear_flag"]
    closes: int = Field(1, ge=1, le=5, description="breakout: closes in a row beyond the zone")
    fakeout_within: int = Field(5, ge=1, le=30)
    retest_within: int = Field(20, ge=1, le=90)
    candle: Literal["off", "pin", "engulfing", "piercing", "any"] = "off"


class EventsRequest(BaseModel):
    end: int = Field(..., ge=0)
    size: float = Field(0.07, gt=0, le=1)
    concepts: Optional[ConceptFlags] = None
    events: Optional[EventSwitches] = None
