"""
Backtest Service.
Orchestrates backtest execution, benchmark comparison, and trade metrics calculation.
"""
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
from utils.calculation_utils import calculate_trade_metrics, calculate_buy_and_hold

class BacktestService:
    @staticmethod
    def execute_backtest(
        strategy: Any,
        cycle_data: Any,
        initial_capital: float = 100000.0
    ) -> Dict[str, Any]:
        """
        Executes a strategy against a target CycleData instance.
        """
        print("=========================================================================")
        print(f"[BACKTEST SERVICE] Strategy: [{getattr(strategy, 'name', type(strategy).__name__)}] | Target: [{cycle_data.name}]")
        print(f"Date Range: {cycle_data.start_date} to {cycle_data.end_date}")
        print("=========================================================================")
        
        signals, macro_mask, audit = strategy.generate_signals(cycle_data.df_daily, cycle_data.df_1h)
        capital = initial_capital
        position = None
        trades = 0
        trade_records = []
        df = cycle_data.df_1h
        
        # Stop Loss Pct from strategy params or default 8%
        stop_loss_pct = strategy.params.get('stop_loss_pct', 0.08) if hasattr(strategy, 'params') and strategy.params else 0.08
        
        for i in range(len(df)):
            curr_close = df['Close'].iloc[i]
            is_bull = macro_mask.values[i] if hasattr(macro_mask, 'values') else macro_mask[i]
            sig = signals.values[i] if hasattr(signals, 'values') else signals[i]
            
            if position is None:
                if is_bull and sig == 1:
                    position = {'entry_price': curr_close, 'entry_idx': i}
                    trades += 1
            elif position is not None:
                ret = (curr_close - position['entry_price']) / position['entry_price']
                if (not is_bull) or ret <= -stop_loss_pct:
                    pnl = capital * ret
                    capital *= (1 + ret)
                    duration_hours = i - position['entry_idx']
                    trade_records.append({
                        "id": trades,
                        "EntryTime": str(df.index[position['entry_idx']]),
                        "ExitTime": str(df.index[i]),
                        "EntryPrice": float(position['entry_price']),
                        "ExitPrice": float(curr_close),
                        "ReturnPct": float(ret),
                        "PnL": float(pnl),
                        "DurationHours": float(duration_hours)
                    })
                    position = None
                    
        if position is not None:
            ret = (df['Close'].iloc[-1] - position['entry_price']) / position['entry_price']
            pnl = capital * ret
            capital *= (1 + ret)
            duration_hours = (len(df) - 1) - position['entry_idx']
            trade_records.append({
                "id": trades,
                "EntryTime": str(df.index[position['entry_idx']]),
                "ExitTime": str(df.index[-1]),
                "EntryPrice": float(position['entry_price']),
                "ExitPrice": float(df['Close'].iloc[-1]),
                "ReturnPct": float(ret),
                "PnL": float(pnl),
                "DurationHours": float(duration_hours)
            })
            
        metrics = calculate_trade_metrics(
            trades_list=trade_records,
            initial_capital=initial_capital,
            ending_capital=capital,
            bnh_return=cycle_data.bnh_return
        )
        
        status_flag = "YES [PASSED]" if metrics['beats_bnh'] else "NO [BEHIND]"
        print("\n-------------------------------------------------------------------------")
        print(f"OFFICIAL ENGINE OUTPUT FOR [{cycle_data.name}]")
        print("-------------------------------------------------------------------------")
        print(f"  1. NET PROFIT            : ${metrics['net_profit_dollar']:+,.2f} ({metrics['net_return']:+.2f}%)")
        print(f"     - Starting Capital    : ${initial_capital:,.2f}")
        print(f"     - Ending Capital      : ${capital:,.2f}")
        print(f"  2. WIN RATE              : {metrics['win_rate']:.2f}% ({metrics['wins']} wins / {trades} trades)")
        print(f"  3. NUMBER OF TRADES      : {trades} completed trades")
        print(f"  4. AVG TRADE DURATION    : {metrics['avg_dur_hours']:.1f} Hours ({metrics['avg_dur_days']:.1f} Days)")
        print("-------------------------------------------------------------------------")
        print("  5. COMPARED TO BUY & HOLD BENCHMARK:")
        print(f"     - Buy & Hold Return   : {cycle_data.bnh_return:+.2f}%")
        print(f"     - Buy & Hold Ending   : ${metrics['bnh_ending_capital']:,.2f}")
        print(f"     - Net Alpha Return    : {metrics['alpha_return']:+.2f}% (${metrics['alpha_dollar']:+,.2f})")
        print(f"     - Beats Buy & Hold?   : {status_flag}")
        print("=========================================================================\n")
        
        return metrics
