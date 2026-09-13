import os
import sys
import pandas as pd

def print_tradingview_alignment_checklist():
    print("=========================================================================")
    print("[TRADINGVIEW ALIGNMENT CHECKLIST] 4 REASONS WHY TV DISPLAY MAY DIFFER")
    print("=========================================================================")
    print("""
1. EXACT EXCHANGE SYMBOL:
   - In Python, we use global BTC index data (Yahoo / Binance BTC-USD).
   - In TradingView, select 'BINANCE:BTCUSDT' or 'INDEX:BTCUSD'.
   - Avoid low-liquidity exchange tickers (like KuCoin/MEXC) whose wicks trigger fake stop-losses.

2. CHART TIMEFRAME:
   - Set chart resolution to '1H' (1-Hour) or '1D' (Daily).
   - Verify that your TradingView timeframe matches the script's calculation.

3. TRADINGVIEW STRATEGY PROPERTIES TAB:
   Double-click the strategy title on your chart -> Open 'Properties' tab:
   - Initial Capital : $100,000
   - Order Size      : 100% of Equity (or 100% Equity)
   - Pyramiding      : 1 (disabled)
   - Commission      : 0.05%

4. DATE RANGE / DEEP BACKTESTING TAB:
   - Free TradingView accounts show only 5,000 bars.
   - Click 'Strategy Tester' -> Open 'Date Range' filter to select the exact window (e.g. Jan 1, 2026 to Sep 4, 2026).
    """)
    print("=========================================================================\n")

if __name__ == "__main__":
    print_tradingview_alignment_checklist()
