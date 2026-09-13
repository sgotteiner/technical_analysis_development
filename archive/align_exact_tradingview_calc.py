import sys
import os
import pandas as pd

sys.path.append('.')
from backtesting import Backtest
from engine import BacktestExecutionRunner, Engine
from modules.data.data_container import CYCLE_2
from ta.trend import ema_indicator

df_1h = CYCLE_2.df_1h.copy()
df_daily = CYCLE_2.df_daily.copy()

daily_ema50 = ema_indicator(df_daily['Close'], window=50).fillna(0)
ema50_dict = dict(zip(df_daily.index.strftime('%Y-%m-%d'), daily_ema50))
BacktestExecutionRunner.ema50 = [ema50_dict.get(idx.strftime('%Y-%m-%d'), 0.0) for idx in df_1h.index]

from strategies.daily_supertrend_strategy import DailySupertrendStrategy
strat = DailySupertrendStrategy()
signals, macro_bull_mask, audit = strat.generate_signals(df_daily, df_1h)
BacktestExecutionRunner.signals = signals
BacktestExecutionRunner.macro_bull_mask = macro_bull_mask
BacktestExecutionRunner.exit_on_ema50 = True
BacktestExecutionRunner.stop_loss_pct = 0.08

# TRADINGVIEW MATCHING CALCULATION: commission = 0.0005 (0.05%), cash = 100,000
bt = Backtest(df_1h, BacktestExecutionRunner, cash=100000, commission=0.0005)
stats = bt.run()

print("=========================================================================")
print("EXACT TRADINGVIEW ALIGNED BACKTEST RESULTS:")
print("=========================================================================")
print(f"  Net Profit       : {stats['Return [%]']:+.2f}%")
print(f"  Win Rate         : {stats['Win Rate [%]']:.2f}%")
print(f"  Total Trades     : {stats['# Trades']}")
print(f"  Max Drawdown     : {stats['Max. Drawdown [%]']:.2f}%")
print("=========================================================================")
