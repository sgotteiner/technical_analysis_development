import sys
import os

sys.path.append('.')
from engine import Engine
from modules.data.data_container import CYCLE_1, CYCLE_2
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

p = {
    'ema_fast': 20,
    'ema_slow': 50,
    'adx_thresh': 20.0,
    'rsi_thresh': 50.0,
    'position_size': 1.0,
    'stop_loss_pct': 0.08
}

strat1 = DailySupertrendStrategy(name="DailySwing_C1", params=p)
res1 = Engine.run(strat1, CYCLE_1)

strat2 = DailySupertrendStrategy(name="DailySwing_C2", params=p)
res2 = Engine.run(strat2, CYCLE_2)

print("=========================================================================")
print("CYCLE 1 (2017 - 2021) STRATEGY RESULTS:")
print(f"  Win Rate         : {res1['win_rate']:.2f}% ({res1['wins']} wins / {res1['total_trades']} trades)")
print(f"  Net Return       : {res1['net_return']:+.2f}%")
print(f"  Buy & Hold Return: {CYCLE_1.bnh_return:+.2f}%")
print("=========================================================================")

print("\n=========================================================================")
print("CYCLE 2 (2021 - 2026) STRATEGY RESULTS:")
print(f"  Win Rate         : {res2['win_rate']:.2f}% ({res2['wins']} wins / {res2['total_trades']} trades)")
print(f"  Net Return       : {res2['net_return']:+.2f}%")
print(f"  Buy & Hold Return: {CYCLE_2.bnh_return:+.2f}%")
print("=========================================================================")
