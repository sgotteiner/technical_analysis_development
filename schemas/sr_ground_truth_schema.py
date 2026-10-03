"""
What the owner RECORDS: a drawing, a sketch, a verdict on a line the code drew, and a setup.

These are the answer key the algorithm is scored against, so they are deliberately permissive
about settings and strict about shape: a verdict is about a LINE (a price, at a date), never about
the settings that produced it.
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator

LABELS = ["support", "resistance", "pipe", "trendline", "range", "triangle", "flag", "pennant",
          "breakout", "retest", "fakeout"]          # suggestions only; any label is accepted


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
