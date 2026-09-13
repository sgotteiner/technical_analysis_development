import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath("atlas_gic_repo/src"))
sys.path.append(os.path.abspath("."))
from janus import Janus
from modules.data.data_container import CYCLE_1, CYCLE_2

def run_janus_agent_backtest():
    print("=========================================================")
    print("[AGENTIC CORE] JANUS AGENT MULTI-COHORT BACKTEST")
    print("=========================================================")
    
    janus = Janus(cohorts=["Technical_Trend", "News_Sentiment"])
    print(f"Janus Agent initialized with cohorts: {janus.cohorts}")
    
    daily_df = CYCLE_1.df_daily
    news_df = CYCLE_1.news_df
    
    if daily_df.empty:
        print("Cycle data empty.")
        return

    daily_df['EMA50'] = daily_df['Close'].ewm(span=50, adjust=False).mean()
    daily_df['Trend_Bullish'] = daily_df['Close'] > daily_df['EMA50']
    daily_df['Return'] = daily_df['Close'].pct_change().fillna(0)
    
    keywords_bull = ['surge', 'soar', 'buy', 'bull', 'launch', 'record', 'high', 'etf', 'approval']
    keywords_bear = ['crash', 'drop', 'ban', 'bear', 'hack', 'sec', 'down', 'crisis', 'lawsuit']
    
    c1_outcomes = []
    for current_date, row in daily_df.iterrows():
        next_ret = row['Return']
        if not news_df.empty:
            pit_news = news_df[news_df['DATETIME'] <= current_date].tail(10)
            bull_score = sum(pit_news['HEADLINE'].str.lower().str.contains('|'.join(keywords_bull)).sum() for _ in range(1))
            bear_score = sum(pit_news['HEADLINE'].str.lower().str.contains('|'.join(keywords_bear)).sum() for _ in range(1))
        else:
            bull_score, bear_score = 0, 0
            
        tech_dir = "LONG" if row['Trend_Bullish'] else "SHORT"
        news_dir = "LONG" if bull_score >= bear_score else "SHORT"
        
        rec_tech = {"ticker": "BTC", "direction": tech_dir, "conviction": 70, "cohort": "Technical_Trend"}
        rec_news = {"ticker": "BTC", "direction": news_dir, "conviction": 60, "cohort": "News_Sentiment"}
        
        c1_outcomes.append(janus.score_recommendation(rec_tech, next_ret))
        c1_outcomes[-1]["cohort"] = "Technical_Trend"
        
        c1_outcomes.append(janus.score_recommendation(rec_news, next_ret))
        c1_outcomes[-1]["cohort"] = "News_Sentiment"
        
    janus.update_weights(c1_outcomes)
    print(f"Janus Learned Cohort Weights: {janus.cohort_weights}")
    print("=========================================================\n")

if __name__ == "__main__":
    run_janus_agent_backtest()
