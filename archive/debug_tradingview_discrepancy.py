import os
import sys
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
from ta.trend import ema_indicator, adx
from ta.momentum import rsi

sys.path.append(os.path.abspath("."))
from modules.data.data_container import CYCLE_1, CYCLE_2

class TVMtf1HStrategy(Strategy):
    ema_fast = 20
    ema_slow = 50
    adx_thresh = 20.0
    rsi_thresh = 50.0
    stop_loss_pct = 0.10

    def init(self):
        pass

    def next(self):
        pass

def run_mtf_1h_test():
    print("=========================================================================")
    print("[DISCREPANCY RESOLUTION] RUNNING STRATEGY ON 1-HOUR CANDLES (CYCLE 1)")
    print("=========================================================================")

    from strategies import DailySupertrendStrategy
    from engine import Engine

    strat = DailySupertrendStrategy(params={'ema_fast': 20, 'ema_slow': 50, 'adx_thresh': 20.0, 'rsi_thresh': 50.0, 'position_size': 1.5, 'stop_loss_pct': 0.10})
    res = Engine.run(strat, CYCLE_1)

    print("\n-------------------------------------------------------------------------")
    print("ENGINE OUTPUT (1-HOUR EXECUTIONS WITH DAILY REGIME MASK):")
    print(f"Net Return : {res['net_return']:+.2f}%")
    print(f"Win Rate   : {res['win_rate']:.2f}% ({res['wins']} wins / {res['total_trades']} trades)")
    print(f"Avg Duration: {res['avg_dur_days']:.1f} Days ({res['avg_dur_hours']:.1f} Hours)")
    print("-------------------------------------------------------------------------\n")

if __name__ == "__main__":
    run_mtf_1h_test()
