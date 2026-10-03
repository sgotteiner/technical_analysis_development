"""
S/R playground schemas: the live-view request and the owner's ground-truth drawings.
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from modules.shapes.sr_settings import parse_levels, parse_rules

LABELS = ["support", "resistance", "pipe", "trendline", "range", "triangle", "flag", "pennant",
          "breakout", "retest", "fakeout"]          # suggestions only; any label is accepted


class ViewRequest(BaseModel):
    end: int = Field(ge=0, description="index of the 'now' candle")
    levels: Dict[str, Dict]
    rules: Dict = Field(default_factory=dict)
    pairs: int = Field(1, ge=0, le=10, description="pipes per level")
    singles: int = Field(0, ge=0, le=30, description="single lines per level")

    @field_validator("levels")
    @classmethod
    def _levels(cls, v):
        return parse_levels(v)

    @field_validator("rules")
    @classmethod
    def _rules(cls, v):
        parse_rules(v)
        return v


class LinesConfig(BaseModel):
    """Lines through the swing points: how close is a touch, and how many touches a line needs.
    mode "owner": levels from the recent points + their history, and trend lines from the recent
    points only. mode "touches": any line through two points, ranked by touches."""
    mode: Literal["owner", "touches", "moves"] = "owner"
    tol_pct: float = Field(1.5, gt=0, le=20)
    min_touches: int = Field(3, ge=2, le=20)
    max_slope_pct: Optional[float] = Field(None, ge=0, le=20, description="%/day; omit for any slope")
    top: int = Field(5, ge=1, le=50)
    anchor_days: Optional[int] = Field(90, ge=1, le=2000,
                                       description="a line must touch a point from the last N days; None = anywhere")
    max_history: Optional[int] = Field(None, ge=0, le=50,
                                       description="keep only a level's last N visits; None = all of them")
    merge_pct: float = Field(0.0, ge=0, le=30,
                             description="levels within this %% of each other become one line; 0 = off")
    trends_per_side: int = Field(1, ge=1, le=5, description="how many trend lines per side")
    prefer: Literal["recent", "visits"] = Field("recent", description="which cluster wins a crowded area")
    min_visits: int = Field(3, ge=1, le=10, description="visits a cluster needs to be a line")
    target_scale: float = Field(2.5, ge=1, le=6, description="targets use swings this much bigger")
    targets_each_way: int = Field(0, ge=0, le=5,
                                  description="levels above and below price that nothing recent touches; 0 = off")
    age_scale: float = Field(700, ge=30, le=5000,
                             description="mode 'moves': at this age a touch must match the move running now")
    band_pct: Optional[float] = Field(None, gt=0, le=30,
                                      description="mode 'moves': blank = half the swing size, his own rule")


class PointsRequest(BaseModel):
    """Peaks and valleys to draw: at given sizes, or at the size that matches a holding time."""
    end: int = Field(ge=0)
    sizes: List[float] = Field(default_factory=list, max_length=4)
    target_days: Optional[int] = Field(None, ge=1, le=365)
    lookback_days: Optional[int] = Field(None, ge=30, le=5000)
    lines: Optional[LinesConfig] = None

    @field_validator("sizes")
    @classmethod
    def _sizes(cls, v):
        if any(not 0.005 <= s <= 1 for s in v):
            raise ValueError("each size must be between 0.005 and 1")
        return v

    @model_validator(mode="after")
    def _something_to_draw(self):
        if not self.sizes and self.target_days is None:
            raise ValueError("give sizes, a target_days, or both")
        return self


class ZonesRequest(BaseModel):
    """Price zones at a swing size, and the ladder read from the current price."""
    end: int = Field(ge=0)
    size: float = Field(gt=0.005, le=1)
    band_pct: Optional[float] = Field(None, gt=0, le=50, description="default: half the swing size")
    min_visits: int = Field(2, ge=1, le=20)
    n_each: int = Field(3, ge=1, le=10)
    trends: Optional[List[Dict]] = Field(None, description="scoring only: the trend lines on screen")
    tol_pct: Optional[float] = Field(None, gt=0, le=20, description="scoring only: how close counts as found")


class Point(BaseModel):
    time: int = Field(description="unix seconds of the candle")
    price: float = Field(gt=0)


Author = Literal["owner", "claude"]      # only the owner's drawings are ground truth


MAX_SKETCH_POINTS = 500          # a freehand path is thinned on the way in; this is the hard cap

# Why a sketch exists (owner, 2026-10-03: "i want to decide if i sketch to communicate with you and
# forget or to really save it"). "ask" is a throwaway explanation and can be cleared in one go;
# "keep" is his, and is never cleared for him.
Purpose = Literal["keep", "ask"]


class AnnotationIn(BaseModel):
    """A line, a pattern box, or a freehand sketch. The sketch is for EXPLAINING (owner,
    2026-10-03: "i want to be able to explain to you better") - it is never scored as a line."""
    kind: Literal["line", "box", "freehand"]
    label: str = Field(min_length=1, max_length=60)
    points: List[Point] = Field(min_length=2, max_length=MAX_SKETCH_POINTS)
    chart: str = "btc_1d"
    note: str = ""
    author: Author = "owner"
    drawn_at: Optional[int] = Field(None, description="the playground's 'now' when it was drawn")
    purpose: Purpose = "keep"
    group: Optional[str] = Field(None, max_length=40,
                                 description="several strokes explaining one thing share this")

    @model_validator(mode="after")
    def _shape_is_whole(self):
        if self.kind != "freehand" and len(self.points) != 2:
            raise ValueError(f"a {self.kind} is two points, got {len(self.points)}")
        if self.kind == "box":
            a, b = self.points
            if a.time == b.time or a.price == b.price:
                raise ValueError("a box needs two different times and prices")
        return self


class AnnotationPatch(BaseModel):
    model_config = {"extra": "forbid"}
    label: Optional[str] = Field(None, min_length=1, max_length=60)
    note: Optional[str] = None


class JudgementIn(BaseModel):
    """The owner's verdict on a line the code drew (2026-10-03: "if you want me to see and judge
    tell me"). A verdict is about the LINE — a price, at a date — not about the settings that
    produced it, so a later search with other settings is scored against it too. The settings are
    kept only as provenance."""
    kind: Literal["level", "trend"]
    verdict: Literal["good", "bad"]
    price: float = Field(gt=0, description="the line's price at `at`, so trends compare too")
    at: int = Field(description="unix seconds of the 'now' candle it was judged at")
    slope_pct_day: Optional[float] = Field(None, description="trends only")
    note: str = ""
    chart: str = "btc_1d"
    settings: Dict = Field(default_factory=dict, description="provenance: what produced the line")
    replacement: Optional[str] = Field(None, description="id of the line he drew instead of this one")


class JudgementPatch(BaseModel):
    """Why he rejected it, and the line he'd draw instead (owner, 2026-10-03: "if i click x i would
    like to have the option to note why or even draw a replacement")."""
    model_config = {"extra": "forbid"}
    note: Optional[str] = None
    replacement: Optional[str] = None


class SetupIn(BaseModel):
    """A setup: several drawings that belong together, and how the owner would trade them."""
    name: str = Field(min_length=1, max_length=100)
    note: str = ""
    members: List[str] = Field(default_factory=list)
    author: Author = "owner"


class SetupPatch(BaseModel):
    model_config = {"extra": "forbid"}
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    note: Optional[str] = None
    members: Optional[List[str]] = None
