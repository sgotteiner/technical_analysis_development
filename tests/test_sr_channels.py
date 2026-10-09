"""
The TradingView "Support Resistance Channels" script, ported (modules/shapes/sr_channels.py), at his
own date: 2026-09-04, where his three lines are 80,277 (price on it), 96,770 above and 72,799 below.
"""
import pandas as pd
from modules.shapes.sr_channels import sr_channels
from scripts.sr_playground import load_daily

HIS_ZONE_PCT = 2.85


def test_the_channels_hold_his_three_lines_at_2026_09_04():
    df = load_daily()
    end = int(df.index.get_indexer([pd.Timestamp("2026-09-04", tz="UTC")])[0])
    lv = sr_channels(df["High"].to_numpy(), df["Low"].to_numpy(), df["Close"].to_numpy(), end)
    assert len(lv) <= 4
    for his in (80_277, 96_770, 72_799):
        assert any(l["low"] * (1 - HIS_ZONE_PCT / 100) <= his <= l["high"] * (1 + HIS_ZONE_PCT / 100)
                   for l in lv), (his, [(round(l["low"]), round(l["high"])) for l in lv])
