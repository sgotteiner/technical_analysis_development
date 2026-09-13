import pandas as pd
import numpy as np
import ta.trend
import ta.momentum
import ta.volatility
import ta.volume

class IndicatorFactory:
    """
    Dynamic Technical Indicator Factory.
    Wraps all standard technical indicators and allows arbitrary hyperparameter configuration.
    """
    
    @staticmethod
    def create_indicator(name: str, params: dict, df: pd.DataFrame) -> pd.Series:
        """
        Dynamically computes an indicator on df given its name and parameter dict.
        
        Examples:
          IndicatorFactory.create_indicator('rsi', {'window': 14}, df)
          IndicatorFactory.create_indicator('macd', {'window_fast': 12, 'window_slow': 26, 'window_sign': 9}, df)
          IndicatorFactory.create_indicator('bollinger_hband', {'window': 20, 'window_dev': 2}, df)
          IndicatorFactory.create_indicator('supertrend', {'window': 10, 'multiplier': 3.0}, df)
        """
        name_clean = name.lower().strip()
        close = df['Close']
        high = df['High'] if 'High' in df.columns else close
        low = df['Low'] if 'Low' in df.columns else close
        volume = df['Volume'] if 'Volume' in df.columns else pd.Series(1, index=df.index)
        
        # 1. Momentum Indicators
        if name_clean == 'rsi':
            window = params.get('window', 14)
            return ta.momentum.rsi(close, window=window).fillna(50.0)
            
        elif name_clean == 'stoch':
            window = params.get('window', 14)
            smooth_window = params.get('smooth_window', 3)
            return ta.momentum.stoch(high, low, close, window=window, smooth_window=smooth_window).fillna(50.0)
            
        elif name_clean == 'williams_r':
            lbp = params.get('lbp', 14)
            return ta.momentum.williams_r(high, low, close, lbp=lbp).fillna(-50.0)
            
        # 2. Trend Indicators
        elif name_clean == 'ema':
            window = params.get('window', 50)
            return ta.trend.ema_indicator(close, window=window).fillna(close)
            
        elif name_clean == 'sma':
            window = params.get('window', 50)
            return ta.trend.sma_indicator(close, window=window).fillna(close)
            
        elif name_clean == 'macd_diff':
            fast = params.get('window_fast', 12)
            slow = params.get('window_slow', 26)
            sign = params.get('window_sign', 9)
            return ta.trend.macd_diff(close, window_fast=fast, window_slow=slow, window_sign=sign).fillna(0.0)
            
        elif name_clean == 'adx':
            window = params.get('window', 14)
            return ta.trend.adx(high, low, close, window=window).fillna(0.0)

        elif name_clean == 'ichimoku_a':
            n1 = params.get('window1', 9)
            n2 = params.get('window2', 26)
            return ta.trend.ichimoku_a(high, low, window1=n1, window2=n2).fillna(close)

        # 3. Volatility Indicators
        elif name_clean == 'bollinger_hband':
            window = params.get('window', 20)
            dev = params.get('window_dev', 2.0)
            return ta.volatility.bollinger_hband(close, window=window, window_dev=dev).fillna(close)

        elif name_clean == 'bollinger_lband':
            window = params.get('window', 20)
            dev = params.get('window_dev', 2.0)
            return ta.volatility.bollinger_lband(close, window=window, window_dev=dev).fillna(close)

        elif name_clean == 'atr':
            window = params.get('window', 14)
            return ta.volatility.average_true_range(high, low, close, window=window).fillna(0.0)

        elif name_clean == 'keltner_hband':
            window = params.get('window', 20)
            return ta.volatility.keltner_channel_hband(high, low, close, window=window).fillna(close)

        # 4. Volume Indicators
        elif name_clean == 'obv':
            return ta.volume.on_balance_volume(close, volume).fillna(0.0)

        elif name_clean == 'cmf':
            window = params.get('window', 20)
            return ta.volume.chaikin_money_flow(high, low, close, volume, window=window).fillna(0.0)

        else:
            raise ValueError(f"Unknown indicator name: '{name}'. Supported: rsi, stoch, williams_r, ema, sma, macd_diff, adx, ichimoku_a, bollinger_hband, bollinger_lband, atr, keltner_hband, obv, cmf.")

    @staticmethod
    def get_supported_indicators():
        return [
            "rsi", "stoch", "williams_r", "ema", "sma", "macd_diff",
            "adx", "ichimoku_a", "bollinger_hband", "bollinger_lband",
            "atr", "keltner_hband", "obv", "cmf"
        ]
