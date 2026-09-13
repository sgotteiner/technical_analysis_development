"""
Core Strategy Execution Engine.
Maintains full backwards compatibility with legacy API while delegating
to business_logic_services and repositories.
"""
from typing import Any, Dict
import pandas as pd
from business_logic_services.backtest_service import BacktestService
from repositories.market_data_repo import MarketDataRepository
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

repo = MarketDataRepository()

def get_btc_weekly_data() -> pd.DataFrame:
    return repo.get_btc_data("1wk")

def get_btc_daily_data() -> pd.DataFrame:
    return repo.get_btc_data("1d")

def get_btc_intraday_data() -> pd.DataFrame:
    return repo.get_btc_data("1h")

def get_btc_5m_data() -> pd.DataFrame:
    return repo.get_btc_data("5m")

def save_all_btc_datasets(output_dir="data"):
    df_wk = get_btc_weekly_data()
    repo.save_dataframe_to_csv(df_wk, "btc_weekly.csv")
    df_daily = get_btc_daily_data()
    repo.save_dataframe_to_csv(df_daily, "btc_daily.csv")
    df_1h = get_btc_intraday_data()
    repo.save_dataframe_to_csv(df_1h, "btc_1h.csv")
    df_5m = get_btc_5m_data()
    repo.save_dataframe_to_csv(df_5m, "btc_5m.csv")
    print(f"All datasets saved successfully to '{output_dir}'")

class Engine:
    """
    Backwards-compatible Engine interface delegating to BacktestService.
    """
    @staticmethod
    def run(strategy: Any, cycle_data: Any, initial_capital: float = 100000.0) -> Dict[str, Any]:
        return BacktestService.execute_backtest(
            strategy=strategy,
            cycle_data=cycle_data,
            initial_capital=initial_capital
        )

if __name__ == "__main__":
    from modules.data.data_container import CYCLE_1, CYCLE_2
    strat = DailySupertrendStrategy()
    print("\n--- RUNNING CYCLE 1 ---")
    Engine.run(strat, CYCLE_1)
    print("\n--- RUNNING CYCLE 2 ---")
    Engine.run(strat, CYCLE_2)
