"""
Export the labelled BTC market regimes (modules/data/market_regimes.py) to a standalone
chart page: ui/regime_viewer.html (full daily history, each period shaded by its label).

Usage:  python scripts/export_regimes.py
"""
import os
import sys
import json
import pandas as pd

sys.path.append(os.path.abspath("."))
from modules.data.regime_batches import load_regime_sets
from helpers.export_helpers import read_ui_file
from helpers.regime_metrics import period_metrics

UI_DIR = "ui"
TEMPLATE = "regimes.html"
OUTPUT = os.path.join(UI_DIR, "regime_viewer.html")


def build_payload():
    sets = load_regime_sets()
    full = pd.read_csv(os.path.join("data", "btc_1d_extended.csv"), index_col=0)
    full.index = pd.to_datetime(full.index, utc=True)
    candles = [{"time": int(t.timestamp()), "open": round(o, 1), "high": round(h, 1), "low": round(l, 1),
                "close": round(c, 1)}
               for t, o, h, l, c in zip(full.index, full["Open"], full["High"], full["Low"], full["Close"])]
    periods = []
    for s in sets:
        w = s.df_daily.iloc[s.start_daily:]
        p = s.period
        periods.append({
            "name": p.name, "regime": p.regime, "shape": p.shape, "start": p.start, "end": p.end,
            "review": p.review, "note": p.note,
            "start_ts": int(w.index[0].timestamp()), "end_ts": int(w.index[-1].timestamp()),
            "history": s.history_days,
            "start_close": round(float(w["Close"].iloc[0])), "end_close": round(float(w["Close"].iloc[-1])),
            "m": period_metrics(w),
        })
    return candles, periods


def export():
    candles, periods = build_payload()
    html = read_ui_file(UI_DIR, TEMPLATE)
    html = html.replace("/* LIGHTWEIGHT_CHARTS_JS_PLACEHOLDER */", read_ui_file(UI_DIR, "lightweight-charts.js"))
    html = html.replace("/* REGIMES_CSS */", read_ui_file(UI_DIR, "css/regimes.css"))
    html = html.replace("/* REGIME_METRICS_JS */", read_ui_file(UI_DIR, "js/regime_metrics.js"))
    html = html.replace("/* DATA_CANDLES */", json.dumps(candles))
    html = html.replace("/* DATA_PERIODS */", json.dumps(periods))
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Regime viewer exported: {OUTPUT}  ({len(candles)} daily candles, {len(periods)} labelled periods)")


if __name__ == "__main__":
    export()
