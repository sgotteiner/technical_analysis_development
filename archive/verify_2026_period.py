import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath("."))
from engine import Engine
from modules.data.data_container import CYCLE_2
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

def main():
    print("=========================================================================")
    print("[2026 INSIGHT INSPECTION] TESTING STRATEGY EXCLUSIVELY ON 2026 DATA")
    print("=========================================================================")

    p = {
        'ema_fast': 20,
        'ema_slow': 50,
        'adx_thresh': 20.0,
        'rsi_thresh': 50.0,
        'position_size': 1.5,
        'stop_loss_pct': 0.08
    }

    df_1h = CYCLE_2.df_1h.copy()
    df_daily = CYCLE_2.df_daily.copy()

    # Filter strictly for 2026 (Jan 1, 2026 to Sep 4, 2026)
    c_2026_start = "2026-01-01"
    df_1h_2026 = df_1h.loc[df_1h.index >= c_2026_start]
    df_daily_2026 = df_daily.loc[df_daily.index >= c_2026_start]

    print(f"2026 Data Range: {df_1h_2026.index[0].date()} to {df_1h_2026.index[-1].date()}")
    bnh_2026 = ((df_1h_2026['Close'].iloc[-1] / df_1h_2026['Close'].iloc[0]) - 1) * 100

    from modules.data.data_container import CycleData
    c2026_container = CycleData(
        name="2026 Year-to-Date Period",
        start_date=str(df_1h_2026.index[0].date()),
        end_date=str(df_1h_2026.index[-1].date()),
        df_1h=df_1h_2026,
        df_daily=df_daily,  # Pass full daily history for indicator warming
        df_5m=pd.DataFrame(),
        news_df=pd.DataFrame()
    )

    strat = DailySupertrendStrategy(name="DailySwing_2026_Test", params=p)
    res = Engine.run(strat, c2026_container)

    print("\n-------------------------------------------------------------------------")
    print("2026 YTD PERFORMANCE BREAKDOWN:")
    print(f"  Buy & Hold Return: {bnh_2026:+.2f}%")
    print(f"  Strategy Return  : {res['net_return']:+.2f}%")
    print(f"  Win Rate         : {res['win_rate']:.2f}% ({res['wins']} wins / {res['total_trades']} trades)")
    print(f"  Total Trades     : {res['total_trades']}")
    print("-------------------------------------------------------------------------\n")

    print("Trades in 2026:")
    for tr in res['trades_list']:
        print(f" - Trade #{tr['id']}: Entry {tr['EntryTime'].date()} (${tr['EntryPrice']:,.2f}) -> Exit {tr['ExitTime'].date()} (${tr['ExitPrice']:,.2f}) | Ret: {tr['ReturnPct']*100:+.2f}% | PnL: ${tr['PnL']:+,.2f}")

if __name__ == "__main__":
    main()
