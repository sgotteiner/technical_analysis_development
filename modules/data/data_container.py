import os
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CycleData:
    """
    Immutable data container for a single Bitcoin Halving Cycle.
    Encapsulates all price action candles (1h, daily, 5m) and dated news articles.
    """
    name: str
    start_date: str
    end_date: str
    df_1h: pd.DataFrame
    df_daily: pd.DataFrame
    df_5m: pd.DataFrame
    news_df: pd.DataFrame
    start_price: float = field(init=False)
    end_price: float = field(init=False)
    bnh_return: float = field(init=False)

    def __post_init__(self):
        # Calculate Buy & Hold benchmark automatically upon initialization
        if not self.df_1h.empty:
            self.start_price = float(self.df_1h['Close'].iloc[0])
            self.end_price = float(self.df_1h['Close'].iloc[-1])
            self.bnh_return = ((self.end_price / self.start_price) - 1.0) * 100.0
        elif not self.df_daily.empty:
            self.start_price = float(self.df_daily['Close'].iloc[0])
            self.end_price = float(self.df_daily['Close'].iloc[-1])
            self.bnh_return = ((self.end_price / self.start_price) - 1.0) * 100.0
        else:
            self.start_price = 0.0
            self.end_price = 0.0
            self.bnh_return = 0.0

def load_standard_cycle_instances(data_dir="data"):
    """
    Load raw files from data_dir once and return CYCLE_1 and CYCLE_2 instances.
    """
    path_1h = os.path.join(data_dir, "btc_1h_extended.csv")
    path_daily = os.path.join(data_dir, "btc_1d_extended.csv")
    path_5m = os.path.join(data_dir, "btc_5m_extended.csv")
    path_news = os.path.join(data_dir, "btc_historical_news.csv")

    # Load 1H Candles
    if os.path.exists(path_1h):
        df_1h = pd.read_csv(path_1h, index_col=0)
        df_1h.index = pd.to_datetime(df_1h.index, utc=True)
    else:
        df_1h = pd.DataFrame()

    # Load Daily Candles
    if os.path.exists(path_daily):
        df_daily = pd.read_csv(path_daily, index_col=0)
        df_daily.index = pd.to_datetime(df_daily.index, utc=True)
    else:
        df_daily = pd.DataFrame()

    # Load 5M Candles
    if os.path.exists(path_5m):
        df_5m = pd.read_csv(path_5m, index_col=0).tail(50000)
        df_5m.index = pd.to_datetime(df_5m.index, utc=True)
    else:
        df_5m = pd.DataFrame()

    # Load Dated News
    if os.path.exists(path_news):
        news_df = pd.read_csv(path_news)
        news_df['DATETIME'] = pd.to_datetime(news_df['DATETIME'], utc=True)
    else:
        news_df = pd.DataFrame()

    # --- INSTANCE 1: CYCLE 1 (2017-08-17 to 2021-11-09) ---
    c1_start, c1_end = "2017-08-17", "2021-11-09"
    cycle_1 = CycleData(
        name="Cycle 1 (Development Phase)",
        start_date=c1_start,
        end_date=c1_end,
        df_1h=df_1h.loc[(df_1h.index >= c1_start) & (df_1h.index <= c1_end)] if not df_1h.empty else pd.DataFrame(),
        df_daily=df_daily.loc[(df_daily.index >= c1_start) & (df_daily.index <= c1_end)] if not df_daily.empty else pd.DataFrame(),
        df_5m=df_5m.loc[(df_5m.index >= c1_start) & (df_5m.index <= c1_end)] if not df_5m.empty else pd.DataFrame(),
        news_df=news_df.loc[(news_df['DATETIME'] >= c1_start) & (news_df['DATETIME'] <= c1_end)] if not news_df.empty else pd.DataFrame(),
    )

    # --- INSTANCE 2: CYCLE 2 (2021-11-10 to 2026-09-04) ---
    c2_start, c2_end = "2021-11-10", "2026-09-04"
    cycle_2 = CycleData(
        name="Cycle 2 (Out-of-Sample Reality Test)",
        start_date=c2_start,
        end_date=c2_end,
        df_1h=df_1h.loc[(df_1h.index >= c2_start) & (df_1h.index <= c2_end)] if not df_1h.empty else pd.DataFrame(),
        df_daily=df_daily.loc[(df_daily.index >= c2_start) & (df_daily.index <= c2_end)] if not df_daily.empty else pd.DataFrame(),
        df_5m=df_5m.loc[(df_5m.index >= c2_start) & (df_5m.index <= c2_end)] if not df_5m.empty else pd.DataFrame(),
        news_df=news_df.loc[(news_df['DATETIME'] >= c2_start) & (news_df['DATETIME'] <= c2_end)] if not news_df.empty else pd.DataFrame(),
    )

    return cycle_1, cycle_2

# Instantiate the two static, immutable global cycle instances
CYCLE_1, CYCLE_2 = load_standard_cycle_instances()
