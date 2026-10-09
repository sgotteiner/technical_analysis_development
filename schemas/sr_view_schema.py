"""
What the playground asks for: the live view, the swing points and the price zones.

The owner's ground truth has its own vocabulary (schemas/sr_ground_truth_schema.py) - no request
ever carries both, which is why they are not one file.
"""
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from modules.shapes.sr_settings import parse_levels, parse_rules


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


class ConceptFlags(BaseModel):
    """mode "concepts": the line concepts, each switched on or off (business_logic_services/line_concepts.py)."""
    swings: Literal["zigzag", "pivots", "atr"] = "zigzag"
    group: Literal["channels", "off"] = "channels"
    band: Literal["move", "range"] = "move"
    parts: List[Literal["pivots", "bars", "sweeps", "round", "measured"]] = ["pivots", "bars", "sweeps"]
    trend: Literal["protected1", "protected2", "window", "off"] = "protected1"
    pick: Literal["roster", "nearest", "strongest"] = "roster"
    per_side: int = Field(1, ge=1, le=5)


class LinesConfig(BaseModel):
    """Lines through the swing points: how close is a touch, and how many touches a line needs.
    mode "owner": levels from the recent points + their history, and trend lines from the recent
    points only. mode "touches": any line through two points, ranked by touches."""
    mode: Literal["owner", "touches", "moves", "channels", "concepts", "zigzag"] = "owner"
    concepts: Optional[ConceptFlags] = None
    tol_pct: float = Field(1.5, gt=0, le=20)
    min_touches: int = Field(3, ge=2, le=20)
    max_slope_pct: Optional[float] = Field(None, ge=0, le=20, description="%/day; omit for any slope")
    top: int = Field(5, ge=1, le=50)
    anchor_days: Optional[int] = Field(90, ge=1, le=2000,
                                       description="a line must touch a point from the last N days; None = anywhere")
    max_history: Optional[int] = Field(None, ge=0, le=50,
                                       description="keep only a level's last N visits; None = all of them")
    merge_pct: float = Field(0.0, ge=0, le=30,
                             description="how wide a level may be, in %%; 0 = take it from the move running now")
    trends_per_side: int = Field(1, ge=1, le=5, description="how many trend lines per side")
    prefer: Literal["recent", "visits"] = Field("recent", description="which cluster wins a crowded area")
    min_visits: int = Field(2, ge=1, le=10,
                            description="visits a cluster needs to be a line; a flat top is two peaks")
    target_scale: float = Field(2.5, ge=1, le=6, description="targets use swings this much bigger")
    targets_each_way: int = Field(0, ge=0, le=5,
                                  description="levels above and below price that nothing recent touches; 0 = off")
    band_pct: Optional[float] = Field(None, gt=0, le=30,
                                      description="mode 'moves': blank = half the swing size, his own rule")


class PointsRequest(BaseModel):
    """Peaks and valleys to draw: at given sizes, or at the size that matches a holding time."""
    end: int = Field(ge=0)
    sizes: List[float] = Field(default_factory=list, max_length=4)
    target_days: Optional[int] = Field(None, ge=1, le=365)
    lookback_days: Optional[int] = Field(None, ge=30, le=5000)
    lines: Optional[LinesConfig] = None
    layers: Optional[Dict[str, bool]] = Field(None, description="what is switched on in his window - logged only")

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
