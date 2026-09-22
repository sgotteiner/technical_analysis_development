"""
Timestamp & Timeframe Alignment Helpers.

The single, no-lookahead way to connect a higher-timeframe (HTF) signal onto
lower-timeframe (LTF) bars. Every cross-timeframe mapping in the codebase must
go through `align_timeframe_signal` so lookahead can never be reintroduced.
"""
import numpy as np
import pandas as pd
from typing import Any


def align_timeframe_signal(
    htf_df: pd.DataFrame,
    ltf_df: pd.DataFrame,
    htf_signal: Any,
    fill_value: Any = False,
) -> np.ndarray:
    """
    Align an HTF signal onto LTF bars with NO lookahead.

    Each LTF bar receives the value of the most recent HTF bar that has already
    CLOSED at that LTF bar's timestamp. An HTF bar timestamped at its open is
    treated as closing at open + interval, where the interval is inferred from
    the HTF index. Works for any timeframe pair (weekly->daily, daily->1h,
    1h->5m, ...).

    Returns an array aligned to `ltf_df` (same length, same order).
    """
    if htf_df.empty or ltf_df.empty:
        return np.full(len(ltf_df), fill_value)

    htf_index = pd.DatetimeIndex(htf_df.index)
    ltf_index = pd.DatetimeIndex(ltf_df.index)

    # HTF bar close = open + one bar interval => the moment the bar's data is known.
    interval = htf_index.to_series().diff().median()
    htf_close = htf_index + interval

    right = pd.DataFrame({"t": htf_close, "v": np.asarray(htf_signal)}).sort_values("t")
    left = pd.DataFrame({"t": ltf_index}).reset_index()  # 'index' preserves LTF order
    left_sorted = left.sort_values("t")

    merged = pd.merge_asof(left_sorted, right, on="t", direction="backward")
    merged = merged.sort_values("index")
    out = merged["v"].to_numpy()

    # LTF bars before the first completed HTF bar have no signal yet.
    na_mask = pd.isna(out)
    if na_mask.any():
        out = out.astype(object)
        out[na_mask] = fill_value

    if isinstance(fill_value, bool):
        out = out.astype(bool)
    return out


# --- Backwards-compatible thin wrappers (now lookahead-safe by delegation) ---
def map_daily_signals_to_intraday(df_daily, df_intraday, daily_mask) -> np.ndarray:
    """Deprecated: use align_timeframe_signal. Kept for backward compatibility."""
    return align_timeframe_signal(df_daily, df_intraday, daily_mask, fill_value=False)


def map_hourly_signals_to_5m(df_1h, df_5m, h1_mask) -> np.ndarray:
    """Deprecated: use align_timeframe_signal. Kept for backward compatibility."""
    return align_timeframe_signal(df_1h, df_5m, h1_mask, fill_value=False)
