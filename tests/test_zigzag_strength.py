"""
Strength of the zigzag's components (business_logic_services/zigzag_strength.py) at his 2022-07-27:
"the horizontal sr lines are really weak ... especially comparing to the trend which is 10 times bigger".
"""
import pandas as pd
from business_logic_services.zigzag_lines import at_day
from scripts.sr_playground import load_daily


def test_each_level_is_measured_against_the_trend():
    df = load_daily()
    g = at_day(df, int(df.index.get_indexer([pd.Timestamp("2022-07-27", tz="UTC")])[0]), 0.07, {})
    down = [t for t in g["trends"] if t["down"]][0]["strength"]
    assert down["size"] > 55                                   # the 2022 fall from the March top: ~63%
    support = [l["strength"] for l in g["levels"] if abs(l["price"] / 20_918 - 1) < 0.01][0]
    assert support["touches"] == 2 and support["held_days"] == 25          # 07-01 and 07-26
    assert abs(support["rel"] - support["size"] / down["size"]) < 1e-9 and support["rel"] < 0.5
