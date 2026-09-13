"""
Backtest API Routes (FastAPI Microservice Endpoints).
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from schemas.backtest_schema import BacktestRequestSchema, BacktestResultSchema
from business_logic_services.backtest_service import BacktestService
from business_logic_services.strategy_service import StrategyService
from modules.data.data_container import CYCLE_1, CYCLE_2

router = APIRouter(prefix="/api/v1/backtest", tags=["Backtesting"])

@router.get("/strategies", response_model=List[str])
def list_strategies():
    """Get list of available registered strategy models."""
    return StrategyService.list_available_strategies()

@router.post("/run", response_model=BacktestResultSchema)
def run_backtest(request: BacktestRequestSchema):
    """Execute strategy backtest against target cycle (CYCLE_1 or CYCLE_2)."""
    try:
        strategy_obj = StrategyService.get_strategy_instance(request.strategy_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cycle_target = request.cycle_target.upper()
    if cycle_target == "CYCLE_1":
        container = CYCLE_1
    elif cycle_target == "CYCLE_2":
        container = CYCLE_2
    else:
        raise HTTPException(status_code=400, detail="Invalid cycle_target. Choose 'CYCLE_1' or 'CYCLE_2'.")

    res = BacktestService.execute_backtest(
        strategy=strategy_obj,
        cycle_data=container,
        initial_capital=request.initial_capital
    )
    
    return BacktestResultSchema(
        net_profit_dollar=res["net_profit_dollar"],
        net_return_pct=res["net_return"],
        win_rate_pct=res["win_rate"],
        wins_count=res["wins"],
        total_trades=res["total_trades"],
        avg_duration_hours=res["avg_dur_hours"],
        avg_duration_days=res["avg_dur_days"],
        bnh_return_pct=res["bnh_return"],
        bnh_ending_capital=res["bnh_ending_capital"],
        alpha_return_pct=res["alpha_return"],
        beats_bnh=res["beats_bnh"],
        trades=res["trades_list"]
    )
