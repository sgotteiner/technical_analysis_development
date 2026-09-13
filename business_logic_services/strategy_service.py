"""
Strategy Business Logic Service.
Handles registry, instantiation, and parameterization of strategy models.
"""
from typing import Dict, Any, Type, List
from strategies.daily_supertrend_strategy import DailySupertrendStrategy
from strategies.agent_confluence_strategy import AgentConfluenceStrategy

STRATEGY_REGISTRY: Dict[str, Type] = {
    "DailySupertrendStrategy": DailySupertrendStrategy,
    "AgentConfluenceStrategy": AgentConfluenceStrategy
}

class StrategyService:
    @staticmethod
    def get_strategy_instance(name: str = "DailySupertrendStrategy", custom_params: Dict[str, Any] = None) -> Any:
        """Instantiate a strategy from registry with optional custom parameters."""
        if name not in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{name}' not found in registry. Available: {list(STRATEGY_REGISTRY.keys())}")
        
        cls = STRATEGY_REGISTRY[name]
        if custom_params:
            return cls(params=custom_params)
        return cls()

    @staticmethod
    def list_available_strategies() -> List[str]:
        """List registered strategy names."""
        return list(STRATEGY_REGISTRY.keys())
