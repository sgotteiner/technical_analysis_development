import os
import sys
import json
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath("."))
from engine import Engine
from modules.data.data_container import CYCLE_1
from strategies.daily_supertrend_strategy import DailySupertrendStrategy

EXPERIMENT_LEDGER_PATH = os.path.join("data", "experiments_ledger.json")

def load_ledger():
    if os.path.exists(EXPERIMENT_LEDGER_PATH):
        with open(EXPERIMENT_LEDGER_PATH, "r") as f:
            return json.load(f)
    return []

def save_ledger(ledger):
    with open(EXPERIMENT_LEDGER_PATH, "w") as f:
        json.dump(ledger, f, indent=2, default=str)

def run_autoresearch_loop(max_runs=5):
    print("=========================================================================")
    print(f"[AGENTIC CORE] AUTORESEARCH GOAL LOOP (MAX RUNS: {max_runs})")
    print("=========================================================================")
    
    ledger = load_ledger()
    best_return = -9999.0
    best_strat = None
    
    grids = [
        {'ema_fast': 20, 'ema_slow': 50, 'adx_thresh': 20.0, 'rsi_thresh': 50.0, 'position_size': 1.5, 'stop_loss_pct': 0.10},
        {'ema_fast': 15, 'ema_slow': 45, 'adx_thresh': 20.0, 'rsi_thresh': 50.0, 'position_size': 1.5, 'stop_loss_pct': 0.10},
        {'ema_fast': 20, 'ema_slow': 50, 'adx_thresh': 25.0, 'rsi_thresh': 55.0, 'position_size': 1.5, 'stop_loss_pct': 0.08},
    ]
    
    for i, g in enumerate(grids[:max_runs]):
        strat = DailySupertrendStrategy(name=f"Autoresearch_Iter_{i+1}", params=g)
        res = Engine.run(strat, CYCLE_1)
        
        if res['net_return'] > best_return:
            best_return = res['net_return']
            best_strat = strat.name
            
        entry = {
            "iteration": len(ledger) + 1,
            "strategy_name": strat.name,
            "hypothesis": f"Autoresearch goal loop iteration {i+1}",
            "params": g,
            "results": res
        }
        ledger.append(entry)
        
    save_ledger(ledger)
    print(f"\nAutoresearch Loop Complete! Best Strategy: {best_strat} ({best_return:+.2f}%)")
    print("=========================================================================\n")

if __name__ == "__main__":
    run_autoresearch_loop(3)
