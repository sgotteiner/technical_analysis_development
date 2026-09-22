"""
Saved regime batches: each accepted period (modules/data/market_regimes.py) is stored as
its own daily-candle file, LEAD_IN_DAYS of preceding data + the batch itself:

    data/regimes/<start>_<regime>_<shape>.csv

The files are versioned with the code, so classifier tests are reproducible even if the
raw data file (data/btc_1d_extended.csv, not versioned) is re-downloaded or changed.
Write them with scripts/save_regime_batches.py.
"""
import os
from dataclasses import dataclass
from typing import List
import pandas as pd
from modules.data.market_regimes import ACCEPTED_PERIODS, LEAD_IN_DAYS, RegimePeriod

BATCH_DIR = os.path.join("data", "regimes")
RAW_DAILY = os.path.join("data", "btc_1d_extended.csv")
COLUMNS = ["Open", "High", "Low", "Close", "Volume"]


@dataclass
class RegimeSet:
    """One labelled batch. `df_daily` = lead-in + batch; the batch starts at row `start_daily`."""
    period: RegimePeriod
    df_daily: pd.DataFrame
    start_daily: int

    @property
    def history_days(self) -> int:
        return self.start_daily

    @property
    def batch(self) -> pd.DataFrame:
        return self.df_daily.iloc[self.start_daily:]


def batch_path(period: RegimePeriod, batch_dir: str = BATCH_DIR) -> str:
    return os.path.join(batch_dir, f"{period.slug}.csv")


def _read(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df


def cut_batch(daily: pd.DataFrame, period: RegimePeriod) -> pd.DataFrame:
    """LEAD_IN_DAYS rows before the period start + the period itself (inclusive)."""
    start = daily.index.get_loc(pd.Timestamp(period.start, tz="UTC"))
    end = daily.index.get_loc(pd.Timestamp(period.end, tz="UTC"))
    if start < LEAD_IN_DAYS:
        raise ValueError(f"{period.name}: only {start} days of data before the batch")
    return daily.iloc[start - LEAD_IN_DAYS:end + 1][COLUMNS]


def save_regime_batches(raw_daily: str = RAW_DAILY, batch_dir: str = BATCH_DIR) -> List[str]:
    daily = _read(raw_daily)
    os.makedirs(batch_dir, exist_ok=True)
    paths = []
    for p in ACCEPTED_PERIODS:
        path = batch_path(p, batch_dir)
        cut_batch(daily, p).to_csv(path)
        paths.append(path)
    return paths


def load_regime_sets(batch_dir: str = BATCH_DIR) -> List[RegimeSet]:
    """Load every accepted batch from its saved file (raises if a file is missing)."""
    return [RegimeSet(p, _read(batch_path(p, batch_dir)), LEAD_IN_DAYS) for p in ACCEPTED_PERIODS]
