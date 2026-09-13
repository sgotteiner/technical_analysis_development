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

strat = DailySupertrendStrategy(name="DailySwing", params=p)
res = Engine.run(strat, CYCLE_2)

print("=========================================================================")
print("EXACT TRADE-BY-TRADE WIN RATE COMPARISON:")
print("=========================================================================")
print(f"Engine.run (Bar Close execution): {res['win_rate']:.2f}% ({res['wins']} wins / {res['total_trades']} trades)")

close_wins = 0
open_wins = 0
total = len(res['trades_list'])

for tr in res['trades_list']:
    ret = tr['ReturnPct'] * 100
    if ret > 0:
        close_wins += 1

print(f"Close Fills: {close_wins} Wins out of {total} Trades ({close_wins/total*100:.1f}%)")
print("=========================================================================")
