"""
Performance Metric Utilities.
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List

def calculate_buy_and_hold(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate Buy & Hold baseline metrics from a price DataFrame."""
    if df.empty or 'Close' not in df.columns:
        return {'start_price': 0.0, 'end_price': 0.0, 'bnh_return': 0.0}
    
    start_price = float(df['Close'].iloc[0])
    end_price = float(df['Close'].iloc[-1])
    bnh_return = ((end_price / start_price) - 1.0) * 100.0 if start_price > 0 else 0.0
    
    return {
        'start_price': start_price,
        'end_price': end_price,
        'bnh_return': bnh_return
    }

def calculate_trade_metrics(
    trades_list: List[Dict[str, Any]],
    initial_capital: float,
    ending_capital: float,
    bnh_return: float
) -> Dict[str, Any]:
    """Summarize trade performance metrics into a standardized result dictionary."""
    total_trades = len(trades_list)
    wins = sum(1 for t in trades_list if t.get('ReturnPct', 0.0) > 0)
    
    win_rate = (wins / total_trades * 100.0) if total_trades > 0 else 0.0
    net_profit_dollar = ending_capital - initial_capital
    net_return = (net_profit_dollar / initial_capital) * 100.0 if initial_capital > 0 else 0.0
    
    durations = [t.get('DurationHours', 0.0) for t in trades_list]
    avg_dur_hours = float(np.mean(durations)) if durations else 0.0
    avg_dur_days = avg_dur_hours / 24.0
    
    returns_pct = [t.get('ReturnPct', 0.0) * 100.0 for t in trades_list]
    mean_return = float(np.mean(returns_pct)) if returns_pct else 0.0
    median_return = float(np.median(returns_pct)) if returns_pct else 0.0
    p33_return = float(np.percentile(returns_pct, 33.33)) if returns_pct else 0.0
    p66_return = float(np.percentile(returns_pct, 66.67)) if returns_pct else 0.0
    min_return = float(np.min(returns_pct)) if returns_pct else 0.0
    max_return = float(np.max(returns_pct)) if returns_pct else 0.0
    std_return = float(np.std(returns_pct)) if returns_pct else 0.0
    
    bnh_profit_dollar = initial_capital * (bnh_return / 100.0)
    bnh_ending_capital = initial_capital + bnh_profit_dollar
    alpha_return = net_return - bnh_return
    alpha_dollar = net_profit_dollar - bnh_profit_dollar
    beats_bnh = net_return > bnh_return
    
    return {
        "net_profit": net_profit_dollar,
        "net_profit_dollar": net_profit_dollar,
        "net_return": net_return,
        "capital": ending_capital,
        "win_rate": win_rate,
        "wins": wins,
        "total_trades": total_trades,
        "trades": total_trades,
        "avg_dur_hours": avg_dur_hours,
        "avg_dur_days": avg_dur_days,
        "avg_duration_hours": avg_dur_hours,
        "avg_duration_days": avg_dur_days,
        "mean_return": mean_return,
        "median_return": median_return,
        "p33_return": p33_return,
        "p66_return": p66_return,
        "min_return": min_return,
        "max_return": max_return,
        "std_return": std_return,
        "bnh_return": bnh_return,
        "bnh_ending_capital": bnh_ending_capital,
        "alpha_return": alpha_return,
        "alpha_dollar": alpha_dollar,
        "beats_bnh": beats_bnh,
        "trades_list": trades_list
    }
