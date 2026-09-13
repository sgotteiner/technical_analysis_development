"""
Strategy Pydantic Schemas.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class StrategyParamsSchema(BaseModel):
    ema_fast: int = Field(20, description="Fast EMA window")
    ema_slow: int = Field(50, description="Slow EMA window")
    adx_thresh: float = Field(20.0, description="ADX filter threshold")
    rsi_thresh: float = Field(50.0, description="RSI filter threshold")
    position_size: float = Field(1.5, description="Position multiplier")
    stop_loss_pct: float = Field(0.08, description="Stop loss percentage")

class StrategySignalResponseSchema(BaseModel):
    strategy_name: str
    total_signals: int
    macro_bull_count: int
    audit_data: Optional[Dict[str, Any]] = None
