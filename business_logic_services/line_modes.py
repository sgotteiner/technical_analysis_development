"""
The two line rules added on 2026-10-08, for the points route: the TradingView S/R Channels script as
it is, and the line concepts as switches. Kept out of the route so it only routes.
"""
from typing import Dict, Optional
import pandas as pd
from business_logic_services.frozen_zigzag import frozen_points
from business_logic_services.line_concepts import Concepts, concept_lines
from business_logic_services.trend_structure import zigzag
from modules.shapes.sr_channels import sr_channels
from business_logic_services.zigzag_view import zigzag_page


def concepts_of(flags) -> Concepts:
    """The request's switches (schemas.ConceptFlags) as the pipeline's settings."""
    return Concepts(**{**flags.model_dump(), "parts": tuple(flags.parts)})


def flags_text(flags) -> str:
    """The concept switches in one short line, for the VIEW log."""
    return (f"swings {flags.swings} | group {flags.group} | band {flags.band} | parts {'+'.join(flags.parts) or '-'}"
            f" | trend {flags.trend} | pick {flags.pick} {flags.per_side}")


def mode_lines(df: pd.DataFrame, end: int, mode: str, flags, size: float, cache: Dict) -> Optional[Dict]:
    """What the page draws for rule "channels" or "concepts"; None for the other rules."""
    if mode == "channels":
        # the script he saw, as it is - no trend, no card
        return {"levels": sr_channels(df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy(), end)}
    if mode == "zigzag":
        return zigzag_page(df, end, size, cache)       # kept lines from the zigzag (zigzag_lines.py)
    if mode != "concepts":
        return None
    out = concept_lines(df, end, concepts_of(flags), size, cache)
    trend = next(iter(out["trends"]), None)
    out["zigzag"] = zigzag(df, end, trend["size"] if trend and "size" in trend else size, cache,
                           frozen_points(df, end, size, cache))
    return out
