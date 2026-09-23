"""Synthetic charts with a known answer, shared by the setup-detector tests."""
import numpy as np
import pandas as pd


def df_from_close(close, wick=0.0):
    c = np.asarray(close, dtype=float)
    idx = pd.date_range("2022-01-01", periods=len(c), freq="D", tz="UTC")
    return pd.DataFrame({"Open": c, "High": c * (1 + wick), "Low": c * (1 - wick), "Close": c}, index=idx)


def legs(start, moves):
    """Close prices from `start` along straight (log) legs: moves = [(price, bars), ...]."""
    out, last = [float(start)], float(start)
    for price, bars in moves:
        out += list(np.exp(np.linspace(np.log(last), np.log(price), bars + 1)[1:]))
        last = price
    return np.array(out)


# Two peaks at 100 (bars 30 and 70), a 30% rejection, a base, then a pole 70 -> 95 and a flag
# that drifts up to 98 — just under the line at 100.
REJECT_THEN_FLAG = [(100, 30), (70, 20), (100, 20), (70, 20), (70, 25), (95, 5), (91, 3), (96, 3), (92, 2), (98, 3), (95, 2)]


def setup_chart(moves=REJECT_THEN_FLAG, start=60):
    return df_from_close(legs(start, moves))
