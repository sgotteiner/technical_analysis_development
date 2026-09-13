"""
Trade Formatter Helpers.
Handles time-series interpolation, marker formatting, and trade audit payloads.
"""
import pandas as pd


def make_smooth_series(daily_s: pd.Series, h1_idx: pd.DatetimeIndex) -> pd.Series:
    """Smooth time-based interpolation for daily series onto hourly candles."""
    s_merged = daily_s.reindex(daily_s.index.union(h1_idx)).sort_index()
    s_interp = s_merged.interpolate(method='time').reindex(h1_idx).ffill().bfill()
    return s_interp


def format_strategy_trades_and_markers(trades_list: list) -> tuple:
    """Format raw engine trade records into chart markers and trade audit payload."""
    markers = []
    formatted_trades = []

    for idx_t, t in enumerate(trades_list):
        try:
            entry_dt = pd.to_datetime(t['EntryTime'])
            exit_dt = pd.to_datetime(t['ExitTime'])
            
            entry_ts = int(entry_dt.timestamp())
            exit_ts = int(exit_dt.timestamp())
            
            if exit_ts <= entry_ts:
                exit_ts = entry_ts + 3600

            ret_pct = float(t.get('ReturnPct', 0.0))
            ret_pct_display = ret_pct * 100.0 if abs(ret_pct) <= 2.0 else ret_pct

            entry_price = float(t.get('EntryPrice', 0.0))
            exit_price = float(t.get('ExitPrice', 0.0))
            dur_hours = float(t.get('DurationHours', 0.0))
            trade_id = int(t.get('id', idx_t + 1))

            markers.append({
                'time': entry_ts,
                'position': 'belowBar',
                'color': '#089981',
                'shape': 'arrowUp',
                'text': ''
            })

            markers.append({
                'time': exit_ts,
                'position': 'aboveBar',
                'color': '#089981' if ret_pct_display >= 0 else '#f23645',
                'shape': 'arrowDown',
                'text': ''
            })

            high_p = max(entry_price, exit_price)
            low_p = min(entry_price, exit_price)
            if high_p == low_p:
                high_p *= 1.001
                low_p *= 0.999

            entry_str = entry_dt.strftime('%Y-%m-%d %H:%M')
            exit_str = exit_dt.strftime('%Y-%m-%d %H:%M')

            formatted_trades.append({
                'id': trade_id,
                'entryTime': entry_str,
                'exitTime': exit_str,
                'entryPrice': entry_price,
                'exitPrice': exit_price,
                'returnPct': ret_pct_display,
                'duration': round(dur_hours, 1),
                'label': f"Trade #{trade_id} ({ret_pct_display:+.1f}%)",
                'fromTime': entry_ts - (86400 * 2),
                'toTime': exit_ts + (86400 * 2),
                'boxTop': [{'time': entry_ts, 'value': high_p}, {'time': exit_ts, 'value': high_p}],
                'boxBottom': [{'time': entry_ts, 'value': low_p}, {'time': exit_ts, 'value': low_p}]
            })
        except Exception:
            continue

    markers.sort(key=lambda x: x['time'])
    return markers, formatted_trades
