"""
Backtest Service.
Runs a strategy over 1H bars: enter when the regime gate is on and a signal
fires, exit on an intrabar stop, a regime flip, or end-of-data. Records exit
reason and MAE/MFE per trade and an equity curve, so a run can be explained.
"""
from typing import Dict, Any
import numpy as np
from utils.calculation_utils import calculate_trade_metrics


def _series(x):
    return x.values if hasattr(x, "values") else x


class BacktestService:
    @staticmethod
    def execute_backtest(strategy: Any, cycle_data: Any, initial_capital: float = 100000.0,
                         verbose: bool = True) -> Dict[str, Any]:
        signals, macro_mask, _ = strategy.generate_signals(cycle_data.df_daily, cycle_data.df_1h)
        signals, macro_mask = _series(signals), _series(macro_mask)
        df = cycle_data.df_1h
        close = df["Close"].values
        high = df["High"].values if "High" in df.columns else close
        low = df["Low"].values if "Low" in df.columns else close

        stop_pct = 0.08
        if hasattr(strategy, "params") and strategy.params:
            stop_pct = strategy.params.get("stop_loss_pct", 0.08)

        capital = initial_capital
        equity_curve = [capital]
        pos = None
        trades = 0
        records = []

        def book(exit_idx, exit_price, reason):
            nonlocal capital, pos
            entry = pos["entry_price"]
            ret = (exit_price - entry) / entry
            pnl = capital * ret
            capital *= (1 + ret)
            equity_curve.append(capital)
            records.append({
                "id": pos["id"],
                "EntryTime": str(df.index[pos["entry_idx"]]),
                "ExitTime": str(df.index[exit_idx]),
                "EntryPrice": float(entry),
                "ExitPrice": float(exit_price),
                "ReturnPct": float(ret),
                "PnL": float(pnl),
                "DurationHours": float(exit_idx - pos["entry_idx"]),
                "ExitReason": reason,
                "MAE": float((pos["min_low"] - entry) / entry),
                "MFE": float((pos["max_high"] - entry) / entry),
            })
            pos = None

        for i in range(len(df)):
            is_bull = bool(macro_mask[i])
            if pos is None:
                if is_bull and signals[i] == 1:
                    trades += 1
                    pos = {"id": trades, "entry_idx": i, "entry_price": close[i],
                           "min_low": low[i], "max_high": high[i]}
                continue

            pos["min_low"] = min(pos["min_low"], low[i])
            pos["max_high"] = max(pos["max_high"], high[i])
            stop_price = pos["entry_price"] * (1 - stop_pct)
            if low[i] <= stop_price:                       # intrabar stop, filled pessimistically
                book(i, stop_price, "stop")
            elif not is_bull:                              # regime flipped off
                book(i, close[i], "regime_off")

        if pos is not None:
            book(len(df) - 1, close[-1], "end")

        metrics = calculate_trade_metrics(
            trades_list=records, initial_capital=initial_capital,
            ending_capital=capital, bnh_return=cycle_data.bnh_return,
            equity_curve=equity_curve,
        )
        if verbose:
            BacktestService._print(strategy, cycle_data, metrics, initial_capital, capital, trades)
        return metrics

    @staticmethod
    def _print(strategy, cycle_data, m, initial, capital, trades):
        flag = "YES [PASSED]" if m["beats_bnh"] else "NO [BEHIND]"
        name = getattr(strategy, "name", type(strategy).__name__)
        print(f"\n[{name}] on [{cycle_data.name}]  ({cycle_data.start_date} -> {cycle_data.end_date})")
        print(f"  Net return   : {m['net_return']:+.2f}%   (${initial:,.0f} -> ${capital:,.0f})")
        print(f"  Max drawdown : {m['max_drawdown']:.2f}%   |  Win rate: {m['win_rate']:.1f}% ({m['wins']}/{trades})")
        print(f"  Median trade : {m['median_return']:+.2f}%  |  Mean: {m['mean_return']:+.2f}%  |  Avg hold: {m['avg_dur_days']:.1f}d")
        print(f"  Buy & Hold   : {m['bnh_return']:+.2f}%   |  Alpha: {m['alpha_return']:+.2f}%   |  Beats B&H: {flag}")
