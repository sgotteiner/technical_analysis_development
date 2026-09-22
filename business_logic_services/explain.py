"""
Strategy explainer.
Turns a backtest result into an attribution trace: how it exited, how much of
each move it captured vs gave back, and where the P&L came from. This is the
signal a human (or later an AI) reads to decide what to improve.
"""
from typing import Dict, Any, List
import numpy as np


def _group_by_reason(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
    out = {}
    for reason in ("stop", "regime_off", "end"):
        subset = [t for t in trades if t.get("ExitReason") == reason]
        if not subset:
            continue
        rets = [t["ReturnPct"] * 100.0 for t in subset]
        out[reason] = {
            "count": len(subset),
            "avg_return_pct": float(np.mean(rets)),
            "total_pnl": float(sum(t["PnL"] for t in subset)),
        }
    return out


def explain_result(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """Build a structured explanation of a backtest result."""
    trades = metrics.get("trades_list", [])
    if not trades:
        return {"summary": "No trades taken.", "by_exit_reason": {}, "give_back": {}}

    # Of the trades that worked, how much of the favourable peak did they keep?
    captured = [t["ReturnPct"] / t["MFE"] for t in trades
                if t["ReturnPct"] > 0 and t.get("MFE", 0) > 0.001]
    avg_capture = float(np.median(captured)) if captured else 0.0

    winners = [t for t in trades if t["ReturnPct"] > 0]
    losers = [t for t in trades if t["ReturnPct"] <= 0]
    pnl_from_top = max((t["PnL"] for t in trades), default=0.0)
    total_pnl = sum(t["PnL"] for t in trades)
    concentration = (pnl_from_top / total_pnl) if total_pnl > 0 else 0.0

    return {
        "trades": len(trades),
        "by_exit_reason": _group_by_reason(trades),
        "give_back": {
            "avg_capture_of_peak": avg_capture,          # 1.0 = exits at the high; 0.3 = gives back 70%
            "avg_mfe_pct": float(np.mean([t["MFE"] * 100 for t in trades])),
            "avg_realized_pct": float(np.mean([t["ReturnPct"] * 100 for t in trades])),
        },
        "risk": {
            "max_drawdown_pct": metrics.get("max_drawdown", 0.0),
            "worst_mae_pct": float(min((t["MAE"] * 100 for t in trades), default=0.0)),
            "pnl_concentration": concentration,          # share of profit from the single best trade
        },
        "wins_losses": {"winners": len(winners), "losers": len(losers)},
    }


def print_explanation(exp: Dict[str, Any]) -> None:
    if not exp.get("by_exit_reason") and not exp.get("trades"):
        print("  (no trades to explain)")
        return
    print("  WHY IT DID WHAT IT DID:")
    gb = exp["give_back"]
    print(f"    - Captured {gb['avg_capture_of_peak']*100:.0f}% of the average favourable move "
          f"(peak +{gb['avg_mfe_pct']:.1f}% -> kept {gb['avg_realized_pct']:+.1f}%)")
    print(f"    - Risk: max drawdown {exp['risk']['max_drawdown_pct']:.1f}%, "
          f"worst dip in a trade {exp['risk']['worst_mae_pct']:.1f}%, "
          f"{exp['risk']['pnl_concentration']*100:.0f}% of profit from one trade")
    print("    - Exits:")
    for reason, s in exp["by_exit_reason"].items():
        print(f"        {reason:11s}: {s['count']:3d} trades, avg {s['avg_return_pct']:+.1f}%, "
              f"pnl ${s['total_pnl']:+,.0f}")
