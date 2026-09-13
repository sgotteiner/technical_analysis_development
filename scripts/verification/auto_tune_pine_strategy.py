import os
import sys
import pandas as pd
import numpy as np
from ta.trend import ema_indicator, adx
from ta.momentum import rsi

sys.path.append(os.path.abspath("."))
from modules.data.data_container import CYCLE_1, CYCLE_2

def run_pine_optimization():
    print("=========================================================================")
    print("[AUTOMATED PINE OPTIMIZER] RUNNING PARAMETER SWEEP FOR HIGH WIN RATE")
    print("=========================================================================\n")

    df_d = CYCLE_1.df_daily.copy()
    if df_d.empty:
        df_d = pd.read_csv("data/btc_1d_extended.csv", index_col=0, parse_dates=True)

    close = df_d['Close']
    high = df_d['High']
    low = df_d['Low']

    fast_spans = [10, 15, 20, 25]
    slow_spans = [30, 45, 50, 60]
    adx_thresholds = [15.0, 20.0, 25.0]
    rsi_thresholds = [45.0, 50.0, 55.0]

    best_winrate = 0.0
    best_return = -999.0
    best_params = None

    results = []

    for f in fast_spans:
        for s in slow_spans:
            if f >= s:
                continue
            for a_th in adx_thresholds:
                for r_th in rsi_thresholds:
                    ema_f = ema_indicator(close, window=f).fillna(0)
                    ema_s = ema_indicator(close, window=s).fillna(0)
                    adx_val = adx(high, low, close, window=14).fillna(0)
                    rsi_val = rsi(close, window=14).fillna(50)

                    # Strict Entry Condition
                    entry_mask = (close > ema_f) & (ema_f > ema_s) & (adx_val > a_th) & (rsi_val > r_th)
                    exit_mask = (close < ema_s)

                    capital = 100000.0
                    position = None
                    trades = 0
                    wins = 0

                    for i in range(len(df_d)):
                        c = close.iloc[i]
                        is_entry = entry_mask.iloc[i]
                        is_exit = exit_mask.iloc[i]

                        if position is None:
                            if is_entry:
                                position = {'entry': c, 'idx': i}
                                trades += 1
                        elif position is not None:
                            ret = (c - position['entry']) / position['entry']
                            if is_exit or ret <= -0.08:
                                capital *= (1 + ret)
                                if ret > 0:
                                    wins += 1
                                position = None

                    net_ret = ((capital - 100000.0) / 100000.0) * 100.0
                    win_rate = (wins / trades * 100.0) if trades > 0 else 0.0

                    if trades >= 10:
                        results.append({
                            'ema_fast': f,
                            'ema_slow': s,
                            'adx_thresh': a_th,
                            'rsi_thresh': r_th,
                            'net_return': net_ret,
                            'win_rate': win_rate,
                            'trades': trades
                        })

                        if win_rate > best_winrate or (win_rate == best_winrate and net_ret > best_return):
                            best_winrate = win_rate
                            best_return = net_ret
                            best_params = {
                                'ema_fast': f,
                                'ema_slow': s,
                                'adx_thresh': a_th,
                                'rsi_thresh': r_th
                            }

    res_df = pd.DataFrame(results).sort_values(by=['win_rate', 'net_return'], ascending=False)
    print("TOP 10 PARAMETER COMBINATIONS ON DAILY BARS:")
    print(res_df.head(10).to_string(index=False))

    print("\n=========================================================================")
    print(f"OPTIMAL PARAMS: EMA({best_params['ema_fast']}/{best_params['ema_slow']}) | ADX > {best_params['adx_thresh']} | RSI > {best_params['rsi_thresh']}")
    print(f"WIN RATE: {best_winrate:.2f}% | NET RETURN: {best_return:+.2f}%")
    print("=========================================================================\n")

    return best_params

if __name__ == "__main__":
    run_pine_optimization()
