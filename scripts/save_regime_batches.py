"""
Save every accepted regime batch (lead-in + batch) to data/regimes/.
Rerun after changing modules/data/market_regimes.py.

Usage:  python scripts/save_regime_batches.py
"""
import os
import sys

sys.path.append(os.path.abspath("."))
from modules.data.regime_batches import save_regime_batches

if __name__ == "__main__":
    for path in save_regime_batches():
        print(f"saved {path}")
