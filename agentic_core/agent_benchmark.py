import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath("."))
from engine import Engine
from modules.data.data_container import CYCLE_1, CYCLE_2
from strategies.agent_confluence_strategy import AgentConfluenceStrategy

def run_agent_benchmark():
    print("=========================================================================")
    print("[AGENTIC CORE] MULTI-TIMEFRAME AGENT CONFLUENCE BENCHMARK")
    print("=========================================================================")
    
    strat = AgentConfluenceStrategy()
    print(f"Executing Agent Strategy: [{strat.name}] on Cycle 1...")
    res1 = Engine.run(strat, CYCLE_1)
    
    print(f"Executing Agent Strategy: [{strat.name}] on Cycle 2...")
    res2 = Engine.run(strat, CYCLE_2)
    
    print("=========================================================================")
    print("AGENT BENCHMARK COMPLETED SUCCESSFULLY!")
    print("=========================================================================\n")

if __name__ == "__main__":
    run_agent_benchmark()
