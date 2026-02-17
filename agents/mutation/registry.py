"""
Mutation Strategy Registry

Registry for managing and accessing mutation strategies.
"""

from typing import Any, Callable, Dict, Optional, Type

from agents.mutation.strategies.synonym import SynonymStrategy
from agents.mutation.strategies.paraphrase import ParaphraseStrategy
from agents.mutation.strategies.role_swap import RoleSwapStrategy
from agents.mutation.strategies.context_obfuscation import ContextObfuscationStrategy
from agents.mutation.strategies.multi_hop import MultiHopStrategy


# Strategy factory type
StrategyFactory = Callable[..., Any]


# Registry of mutation strategies
_MUTATION_STRATEGIES: Dict[str, StrategyFactory] = {
    "synonym_replacement": SynonymStrategy,
    "synonym": SynonymStrategy,
    "paraphrase": ParaphraseStrategy,
    "role_swap": RoleSwapStrategy,
    "role": RoleSwapStrategy,
    "context_obfuscation": ContextObfuscationStrategy,
    "context": ContextObfuscationStrategy,
    "multi_hop": MultiHopStrategy,
    "multi": MultiHopStrategy,
}


def register_mutation_strategy(name: str, factory: StrategyFactory) -> None:
    """
    Register a new mutation strategy.
    
    Args:
        name: Strategy name
        factory: Strategy factory function
    """
    _MUTATION_STRATEGIES[name.lower()] = factory


def get_mutation_strategy(name: str, **kwargs: Any) -> Optional[Any]:
    """
    Get a mutation strategy by name.
    
    Args:
        name: Strategy name
        **kwargs: Strategy parameters
        
    Returns:
        Strategy instance or None if not found
    """
    factory = _MUTATION_STRATEGIES.get(name.lower())
    if factory is None:
        return None
    
    return factory(**kwargs)


def list_mutation_strategies() -> list[str]:
    """
    Get list of available mutation strategies.
    
    Returns:
        List of strategy names
    """
    return list(_MUTATION_STRATEGIES.keys())


def get_default_strategies() -> list[str]:
    """
    Get list of default strategy names.
    
    Returns:
        List of default strategy names
    """
    return [
        "synonym_replacement",
        "paraphrase", 
        "role_swap",
        "context_obfuscation",
        "multi_hop",
    ]


def create_strategy_from_config(config: dict[str, Any]) -> Optional[Any]:
    """
    Create a strategy from configuration dict.
    
    Args:
        config: Configuration dict with 'name' and optional 'params'
        
    Returns:
        Strategy instance or None
    """
    name = config.get("name")
    if not name:
        return None
    
    params = config.get("params", {})
    return get_mutation_strategy(name, **params)


__all__ = [
    "register_mutation_strategy",
    "get_mutation_strategy",
    "list_mutation_strategies",
    "get_default_strategies",
    "create_strategy_from_config",
    "StrategyFactory",
]
