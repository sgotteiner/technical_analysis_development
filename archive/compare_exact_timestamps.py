import sys
import os
import pandas as pd

sys.path.append('.')
from engine import Engine
from modules.data.data_container import CYCLE_2
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

p = {
    'ema_fast': 20,
    'ema_slow': 50,
    'adx_thresh': 20.0,
    'rsi_thresh': 50.0,
    'position_size': 1.0,
    'stop_loss_pct': 0.08
}

df_1h = CYCLE_2.df_1h.copy()
df_daily = CYCLE_2.df_daily.copy()

c_2026_start = "2026-01-01"
df_1h_2026 = df_1h.loc[df_1h.index >= c_2026_start]

from modules.data.data_container import CycleData
c2026_container = CycleData(
    name="2026 Year-to-Date Period",
    start_date=str(df_1h_2026.index[0].date()),
    end_date=str(df_1h_2026.index[-1].date()),
    df_1h=df_1h_2026,
    df_daily=df_daily,
    df_5m=pd.DataFrame(),
    news_df=pd.DataFrame()
)

strat = DailySupertrendStrategy(name="DailySwing", params=p)
res = Engine.run(strat, c2026_container)

print("=========================================================================")
print("EXACT PYTHON ENGINE TRADE LIST (2026 YTD):")
print("=========================================================================")
for tr in res['trades_list']:
    print(f"Trade #{tr['id']}:")
    print(f"  Entry: {tr['EntryTime']} @ ${tr['EntryPrice']:,.2f}")
    print(f"  Exit : {tr['ExitTime']} @ ${tr['ExitPrice']:,.2f}")
    print(f"  Return: {tr['ReturnPct']*100:+.2f}% | Keys: {list(tr.keys())}")
    print("-" * 50)
