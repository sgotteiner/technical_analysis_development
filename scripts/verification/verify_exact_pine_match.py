import os
import sys

# Ensure project root is in python path when running from scripts/verification/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import pandas as pd
import numpy as np

from engine import Engine
from modules.data.data_container import CYCLE_1, CYCLE_2
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

def main():
    print("=========================================================================")
    print("[EXACT STRATEGY VERIFICATION] 88.64% WIN RATE SWING STRATEGY")
    print("=========================================================================")
    
    # Original exact strategy parameters from Cycle 1 development
    p = {
        'ema_fast': 20,
        'ema_slow': 50,
        'adx_thresh': 20.0,
        'rsi_thresh': 50.0,
        'position_size': 1.5,
        'stop_loss_pct': 0.08
    }
    
    strat = DailySupertrendStrategy(name="DailySwing_EMA20_50_ADX20_RSI50", params=p)
    
    print("\n--- 1. CYCLE 1 IN-SAMPLE DEVELOPMENT RESULT ---")
    res1 = Engine.run(strat, CYCLE_1)
    
    print("\n--- 2. CYCLE 2 OUT-OF-SAMPLE REALITY TEST RESULT ---")
    res2 = Engine.run(strat, CYCLE_2)
    
    print("\n=========================================================================")
    print(f"CYCLE 1 : Return: {res1['net_return']:+.2f}% | Win Rate: {res1['win_rate']:.2f}% ({res1['wins']}/{res1['total_trades']})")
    print(f"CYCLE 2 : Return: {res2['net_return']:+.2f}% | Win Rate: {res2['win_rate']:.2f}% ({res2['wins']}/{res2['total_trades']})")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()
