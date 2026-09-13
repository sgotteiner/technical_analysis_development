"""
Market Data Repository.
Handles all external market data network calls (Yahoo Finance) and local storage integration.
"""
import os
import requests
import pandas as pd
from typing import Optional
from config.settings import settings

class MarketDataRepository:
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = data_dir or settings.data_dir
        os.makedirs(self.data_dir, exist_ok=True)

    def fetch_yahoo_chart(self, symbol: str, interval: str = "1d", range_str: str = "10y") -> pd.DataFrame:
        """Fetch OHLCV price chart data from Yahoo Finance REST API."""
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{symbol}?interval={interval}&range={range_str}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
        data = r.json()
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        df = pd.DataFrame({
            'Open': quote['open'],
            'High': quote['high'],
            'Low': quote['low'],
            'Close': quote['close'],
            'Volume': quote['volume']
        }, index=pd.to_datetime(timestamps, unit='s', utc=True))
        
        df = df.dropna()
        return df

    def get_btc_data(self, interval: str = "1d") -> pd.DataFrame:
        """Helper to get BTC-USD data for specific interval."""
        range_map = {
            "1wk": "max",
            "1d": "10y",
            "1h": "730d",
            "5m": "60d"
        }
        r_str = range_map.get(interval, "10y")
        return self.fetch_yahoo_chart("BTC-USD", interval=interval, range_str=r_str)

    def save_dataframe_to_csv(self, df: pd.DataFrame, filename: str) -> str:
        """Save a market dataframe to CSV in the data directory."""
        filepath = os.path.join(self.data_dir, filename)
        df.to_csv(filepath)
        return filepath
