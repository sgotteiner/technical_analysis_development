import os
import sys
import argparse
import pandas as pd

sys.path.append(os.path.abspath("."))
from business_logic_services.backtest_service import BacktestService
from repositories.market_data_repo import MarketDataRepository
from modules.data.data_container import CYCLE_1, CYCLE_2, CycleData
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

market_repo = MarketDataRepository()

def run_asset_test(symbol: str, name: str, category: str = "Stock"):
    print(f"\nFetching daily data for {name} ({symbol})...")
    try:
        df_daily = market_repo.fetch_yahoo_chart(symbol, interval="1d", range_str="10y")
        if df_daily.empty or len(df_daily) < 50:
            print(f"Skipping {symbol}: Insufficient data.")
            return None
            
        container = CycleData(
            name=f"{name} ({symbol})",
            start_date=str(df_daily.index[0].date()),
            end_date=str(df_daily.index[-1].date()),
            df_1h=df_daily,
            df_daily=df_daily,
            df_5m=pd.DataFrame(),
            news_df=pd.DataFrame()
        )
        
        strategy = DailySupertrendStrategy(name=f"DailySwing_{symbol}")
        res = BacktestService.execute_backtest(strategy, container)
        res['symbol'] = symbol
        res['name'] = name
        res['category'] = category
        return res
    except Exception as e:
        print(f"Error executing backtest for {symbol}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Unified Backtest Engine Runner")
    parser.add_argument("--mode", type=str, choices=["cycle1", "cycle2", "equity", "multi", "all"], default="all")
    args = parser.parse_args()

    mode = args.mode
    strat = DailySupertrendStrategy()

    print("=========================================================================")
    print(f"[UNIFIED BACKTEST ENGINE] EXECUTION MODE: [{mode.upper()}]")
    print("=========================================================================\n")

    if mode in ["cycle1", "all"]:
        print(">>> RUNNING BITCOIN CYCLE 1 (DEVELOPMENT DATASET)...")
        BacktestService.execute_backtest(strat, CYCLE_1)

    if mode in ["cycle2", "all"]:
        print(">>> RUNNING BITCOIN CYCLE 2 (OUT-OF-SAMPLE DATASET)...")
        BacktestService.execute_backtest(strat, CYCLE_2)

    if mode in ["equity", "all"]:
        print(">>> RUNNING EQUITIES BENCHMARK (SPY & GOOGL)...")
        run_asset_test("SPY", "S&P 500 ETF", "Index ETF")
        run_asset_test("GOOGL", "Alphabet Inc.", "Big Tech Stock")

    if mode in ["multi", "all"]:
        print(">>> RUNNING MULTI-MARKET & CRASHED ASSETS STRESS TEST...")
        assets = [
            ("ETH-USD", "Ethereum", "Mid/Large Crypto"),
            ("SOL-USD", "Solana", "Mid/Large Crypto"),
            ("ALGO-USD", "Algorand", "Crashed Crypto"),
            ("ICP-USD", "Internet Computer", "Crashed Crypto"),
            ("FTT-USD", "FTX Token", "Dead Crypto"),
            ("PLTR", "Palantir Tech", "Mid-Cap Stock"),
            ("AMD", "AMD", "Mid-Cap Stock"),
            ("PTON", "Peloton", "Crashed Stock"),
            ("SNAP", "Snap Inc.", "Crashed Stock")
        ]
        for sym, name, cat in assets:
            run_asset_test(sym, name, cat)

    print("=========================================================================")
    print("ALL REQUESTED BACKTESTS COMPLETED SUCCESSFULLY!")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()
