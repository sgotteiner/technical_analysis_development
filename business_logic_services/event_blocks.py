"""
Events as strategy blocks: the bridge from the events layer to ComposableStrategy (owner, 2026-10-08:
"choose the specific breakout pattern or patterns with flags and assemble full strategies").

An EventBlock fires on the daily bar an event of its kind was decided, the way it points. A strategy
combines blocks the way it already does (ALL / ANY / N of M), on the trading timeframe, through the
one no-lookahead aligner - e.g. "breakout up AND a bullish candle", or "fakeout down OR double top".
"""
from typing import Dict, Iterable, Optional
import numpy as np
from business_logic_services.event_service import EventFlags, compute_events
from business_logic_services.line_concepts import Concepts
from modules.base import BaseBlock, BlockResult

_CACHE: Dict = {}            # the events of a setting are computed once per process


class EventBlock(BaseBlock):
    def __init__(self, kinds: Iterable[str], direction: Optional[str] = None,
                 concepts: Concepts = Concepts(), flags: EventFlags = EventFlags(), size: float = 0.07):
        kinds = tuple(kinds)
        super().__init__(name=f"{'/'.join(kinds)} {direction or 'any way'}", category="Event", tf="1D")
        self.kinds, self.direction = kinds, direction
        self.concepts, self.flags, self.size = concepts, flags, size

    def evaluate(self, df_daily, df_1h) -> BlockResult:
        events = compute_events(df_daily, self.concepts, self.size, self.flags, _CACHE)
        mask = np.zeros(len(df_daily), dtype=bool)
        visual = {}
        for e in events:
            if e["type"] in self.kinds and (self.direction is None or e["direction"] == self.direction):
                mask[e["bar"]] = True
                visual[e["bar"]] = {"start_idx": e["from_bar"], "end_idx": e["bar"], "name": e["type"],
                                    "why": e["why"]}
        return BlockResult(self.name, self.category, self.tf, mask, visual_data=visual)
