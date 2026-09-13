import os
import sys
import json
import argparse
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

def main():
    parser = argparse.ArgumentParser(description="Run N Iterations of Strategy Parameter Optimization on Cycle 1")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations to run (default: 5)")
    args = parser.parse_args()

    num_iterations = args.iterations

    print("=========================================================================")
    print(f"[AUTORESEARCH ENGINE] RUNNING {num_iterations} ITERATIONS OF STRATEGY OPTIMIZATION")
    print("=========================================================================")
    print(f"Target Dataset : {CYCLE_1.name} ({CYCLE_1.start_date} to {CYCLE_1.end_date})")
    print(f"Buy & Hold    : {CYCLE_1.bnh_return:+.2f}%")
    print("=========================================================================\n")

    ledger = load_ledger()

    # Pre-defined parameter grids for iterative discovery
    param_configs = [
        {'ema_fast': 20, 'ema_slow': 50, 'adx_thresh': 20.0, 'rsi_thresh': 50.0, 'position_size': 1.5, 'stop_loss_pct': 0.10},
        {'ema_fast': 15, 'ema_slow': 45, 'adx_thresh': 22.0, 'rsi_thresh': 52.0, 'position_size': 1.5, 'stop_loss_pct': 0.08},
        {'ema_fast': 20, 'ema_slow': 50, 'adx_thresh': 25.0, 'rsi_thresh': 55.0, 'position_size': 1.5, 'stop_loss_pct': 0.08},
        {'ema_fast': 10, 'ema_slow': 30, 'adx_thresh': 20.0, 'rsi_thresh': 50.0, 'position_size': 1.25, 'stop_loss_pct': 0.08},
        {'ema_fast': 25, 'ema_slow': 60, 'adx_thresh': 20.0, 'rsi_thresh': 50.0, 'position_size': 1.5, 'stop_loss_pct': 0.10},
    ]

    for i in range(min(num_iterations, len(param_configs))):
        cfg = param_configs[i]
        strat_name = f"Iter{i+1}_Supertrend_F{cfg['ema_fast']}_S{cfg['ema_slow']}_ADX{int(cfg['adx_thresh'])}"
        print(f"\n-------------------------------------------------------------------------")
        print(f"ITERATION #{i+1}: Strategy [{strat_name}]")
        print(f"Params: EMA({cfg['ema_fast']}/{cfg['ema_slow']}) | ADX > {cfg['adx_thresh']} | RSI > {cfg['rsi_thresh']}")
        print(f"-------------------------------------------------------------------------")

        strat = DailySupertrendStrategy(name=strat_name, params=cfg)
        res = Engine.run(strat, CYCLE_1)

        entry = {
            "iteration": len(ledger) + 1,
            "strategy_name": strat.name,
            "hypothesis": f"Iteration {i+1} testing EMA({cfg['ema_fast']}/{cfg['ema_slow']}) with ADX>{cfg['adx_thresh']} filter",
            "params": cfg,
            "results": res,
            "insight": f"Net Return: {res['net_return']:+.2f}%, Win Rate: {res['win_rate']:.2f}%, Trades: {res['total_trades']}"
        }
        ledger.append(entry)

    save_ledger(ledger)
    print("\n=========================================================================")
    print(f"{num_iterations}-ITERATION RUN COMPLETE & SAVED TO 'data/experiments_ledger.json'")
    print("=========================================================================\n")

if __name__ == "__main__":
    main()
