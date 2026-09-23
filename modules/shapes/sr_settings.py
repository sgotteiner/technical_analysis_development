"""
S/R rule settings — every rule of the S/R lines / pipes definition that the playground lets the
owner change (2026-09-22). Defaults are the rules as built (docs/SR_LINES_DESIGN.md), with whose
rule each one is:

  touch_pct        "close to the line", % .......................... 1.5   Claude
  candidate_ratio  candidate zigzag = magnitude x ratio ............ 0.5   Claude
  both_sides       a touch is significant only if price was >= magnitude away from the line
                   before AND after it (False: one side is enough) .. True  Claude
  min_touches      significant touches for a line .................. 2     (open question 4)
  max_divergence   upper slope - lower slope, log/day; 0 = never widens   owner
  min_width_q      pipe >= this quantile of the swing legs; 0 = off . 0.5 (median)  Claude
  max_width_mult   pipe <= this x the largest swing ................ 1.0   owner
  act_together     both lines' touch periods overlap ............... True  Claude
  check_now        width rules also hold at "now" .................. True  Claude

Levels: {name: {"period": days, "magnitude": fraction}}, any number of them.
"""
from dataclasses import dataclass, fields, asdict
from typing import Dict
import numpy as np

DEFAULT_LEVELS = {"higher": {"period": 400, "magnitude": 0.20},
                  "lower": {"period": 100, "magnitude": 0.10}}


@dataclass(frozen=True)
class SRRules:
    touch_pct: float = 1.5
    candidate_ratio: float = 0.5
    both_sides: bool = True
    min_touches: int = 2
    max_divergence: float = 0.0
    min_width_q: float = 0.5
    max_width_mult: float = 1.0
    act_together: bool = True
    check_now: bool = True

    @property
    def tol(self) -> float:
        return float(np.log(1 + self.touch_pct / 100))

    def as_dict(self) -> Dict:
        return asdict(self)


DEFAULT_RULES = SRRules()

_BOUNDS = {"touch_pct": (0.0, 50.0, True), "candidate_ratio": (0.0, 1.0, False), "min_touches": (2, 50, True),
           "max_divergence": (0.0, 1.0, True), "min_width_q": (0.0, 1.0, True), "max_width_mult": (0.0, 20.0, False)}


def parse_rules(raw: Dict) -> SRRules:
    """SRRules from a (partial) dict; ValueError on unknown keys or out-of-range values."""
    types = {f.name: f.type for f in fields(SRRules)}
    unknown = set(raw) - set(types)
    if unknown:
        raise ValueError(f"unknown rules: {sorted(unknown)}")
    vals = {}
    for k, v in raw.items():
        vals[k] = types[k](v)
        if k in _BOUNDS:
            lo, hi, lo_incl = _BOUNDS[k]
            if not ((vals[k] >= lo if lo_incl else vals[k] > lo) and vals[k] <= hi):
                raise ValueError(f"{k}={v} outside {'[' if lo_incl else '('}{lo}, {hi}]")
    return SRRules(**vals)


def parse_levels(raw: Dict) -> Dict[str, Dict]:
    """Validated levels, order kept; ValueError on an empty set, bad names or values."""
    if not raw:
        raise ValueError("at least one level is needed")
    out = {}
    for name, cfg in raw.items():
        if not str(name).strip() or set(cfg) != {"period", "magnitude"}:
            raise ValueError(f"level {name!r} needs a name, a period and a magnitude")
        period, magnitude = int(cfg["period"]), float(cfg["magnitude"])
        if not 10 <= period <= 5000 or not 0 < magnitude <= 5:
            raise ValueError(f"level {name!r}: period 10-5000 days, magnitude in (0, 5]")
        out[str(name)] = {"period": period, "magnitude": magnitude}
    return out
