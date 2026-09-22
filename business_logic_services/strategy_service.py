"""
Strategy Business Logic Service.
Handles registry, instantiation, and parameterization of strategy models.
Enforces that every registered strategy extends BaseStrategy, so no strategy
can hand-roll its own (potentially lookahead-prone) timeframe mapping.
"""
from typing import Dict, Any, Type, List
from strategies.base_strategy import BaseStrategy
from strategies.daily_supertrend_strategy import DailySupertrendStrategy
from strategies.agent_confluence_strategy import AgentConfluenceStrategy
from strategies.composable_strategy import ComposedSupertrendStrategy

STRATEGY_REGISTRY: Dict[str, Type] = {
    "DailySupertrendStrategy": DailySupertrendStrategy,
    "AgentConfluenceStrategy": AgentConfluenceStrategy,
    "ComposedSupertrendStrategy": ComposedSupertrendStrategy,
}

# Validate the whole registry at import: reject anything not extending BaseStrategy.
for _name, _cls in STRATEGY_REGISTRY.items():
    if not (isinstance(_cls, type) and issubclass(_cls, BaseStrategy)):
        raise TypeError(
            f"Strategy '{_name}' must extend BaseStrategy to use the no-lookahead "
            f"aligner. Got {_cls!r}."
        )


class StrategyService:
    @staticmethod
    def get_strategy_instance(name: str = "DailySupertrendStrategy", custom_params: Dict[str, Any] = None) -> Any:
        """Instantiate a strategy from registry with optional custom parameters."""
        if name not in STRATEGY_REGISTRY:
            raise ValueError(f"Strategy '{name}' not found in registry. Available: {list(STRATEGY_REGISTRY.keys())}")

        cls = STRATEGY_REGISTRY[name]
        instance = cls(params=custom_params) if custom_params else cls()
        if not isinstance(instance, BaseStrategy):
            raise TypeError(f"Strategy '{name}' must be a BaseStrategy instance.")
        return instance

    @staticmethod
    def list_available_strategies() -> List[str]:
        """List registered strategy names."""
        return list(STRATEGY_REGISTRY.keys())
