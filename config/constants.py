"""
Configuration Constants for Trading Systems & Microservices.
"""

# Cycle Date Boundaries
CYCLE_1_START = "2017-08-17"
CYCLE_1_END = "2021-11-09"
CYCLE_1_NAME = "Cycle 1 (Development Phase)"

CYCLE_2_START = "2021-11-10"
CYCLE_2_END = "2026-09-04"
CYCLE_2_NAME = "Cycle 2 (Out-of-Sample Reality Test)"

# Default Strategy Parameters
DEFAULT_DAILY_SUPERTREND_PARAMS = {
    'ema_fast': 20,
    'ema_slow': 50,
    'adx_thresh': 20.0,
    'rsi_thresh': 50.0,
    'position_size': 1.5,
    'stop_loss_pct': 0.08
}

DEFAULT_INTRADAY_SCALP_PARAMS = {
    'ema_fast_h1': 20,
    'ema_slow_h1': 50,
    'adx_thresh_h1': 20.0,
    'rsi_thresh_h1': 50.0,
    'ema_fast_m5': 20,
    'ema_slow_m5': 50,
    'rsi_thresh_m5': 50.0,
    'stop_loss_pct': 0.02
}

# API Defaults
DEFAULT_YAHOO_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DEFAULT_CDP_PORT = 9222
