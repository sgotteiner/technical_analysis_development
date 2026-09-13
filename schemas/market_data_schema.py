"""
Market Data & OHLCV Request/Response Schemas.
"""
from typing import List, Optional
from pydantic import BaseModel, Field

class MarketDataRequestSchema(BaseModel):
    symbol: str = Field("BTC-USD", description="Asset ticker symbol")
    interval: str = Field("1d", description="Candle interval (1d, 1h, 5m, 1wk)")
    range_str: str = Field("10y", description="Time range (e.g. 10y, 730d, max)")

class OHLCVItemSchema(BaseModel):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float

class MarketDataResponseSchema(BaseModel):
    symbol: str
    interval: str
    candle_count: int
    start_date: str
    end_date: str
    data: Optional[List[OHLCVItemSchema]] = None
