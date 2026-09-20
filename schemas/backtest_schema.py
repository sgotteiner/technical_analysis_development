"""
Backtest Execution & Results Schemas.
"""
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field

class BacktestRequestSchema(BaseModel):
    strategy_name: str = Field("DailySupertrendStrategy", description="Strategy class name")
    cycle_target: str = Field("CYCLE_1", description="Target cycle identifier (CYCLE_1, CYCLE_2, or custom)")
    initial_capital: float = Field(100000.0, description="Starting capital in USD")

class TradeRecordSchema(BaseModel):
    id: int
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    return_pct: float
    pnl: float
    duration_hours: float

class BacktestResultSchema(BaseModel):
    net_profit_dollar: float
    net_return_pct: float
    win_rate_pct: float
    wins_count: int
    total_trades: int
    avg_duration_hours: float
    avg_duration_days: float
    mean_return_pct: float = 0.0
    median_return_pct: float = 0.0
    p33_return_pct: float = 0.0
    p66_return_pct: float = 0.0
    min_return_pct: float = 0.0
    max_return_pct: float = 0.0
    bnh_return_pct: float
    bnh_ending_capital: float
    alpha_return_pct: float
    beats_bnh: bool
    trades: List[Dict[str, Any]] = []
