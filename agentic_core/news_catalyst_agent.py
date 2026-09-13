import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath("."))
from modules.data.data_container import CYCLE_1

def analyze_news_catalysts():
    print("=========================================================")
    print("[AGENTIC CORE] HIGH QUALITY NEWS CATALYST AGENT")
    print("=========================================================")
    
    news_df = CYCLE_1.news_df
    if news_df.empty:
        print("No historical news dataset found.")
        return
        
    print(f"Total News Articles Analyzed: {len(news_df)}")
    high_impact = news_df[abs(news_df['SENTIMENT_SCORE']) > 0.05]
    print(f"High-Impact Catalysts Detected: {len(high_impact)}")
    
    for idx, row in high_impact.iterrows():
        date_str = str(row['DATETIME'].date()) if hasattr(row['DATETIME'], 'date') else str(row['DATETIME'])
        print(f"  [{date_str}] Score: {row['SENTIMENT_SCORE']:+.2f} | Headline: {row['HEADLINE']}")
    print("=========================================================\n")

if __name__ == "__main__":
    analyze_news_catalysts()
