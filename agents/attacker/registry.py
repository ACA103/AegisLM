"""
Attack Strategy Registry

Plugin system for attack strategies.
"""

from typing import Dict

from agents.attacker.base import (
    BaseAttackStrategy,
    BiasTriggerStrategy,
    ChainingStrategy,
    ContextPoisoningStrategy,
    JailbreakStrategy,
    PromptInjectionStrategy,
    RoleConfusionStrategy,
)
from agents.attacker.strategies.bias_trigger import BiasTriggerAttack
from agents.attacker.strategies.chaining import ChainingAttack
from agents.attacker.strategies.context_poison import ContextPoisoningAttack
from agents.attacker.strategies.injection import InjectionAttack
from agents.attacker.strategies.jailbreak import JailbreakAttack
from agents.attacker.strategies.role_confusion import RoleConfusionAttack


# Global registry of attack strategies
ATTACK_REGISTRY: Dict[str, BaseAttackStrategy] = {}


def register_attack_strategy(name: str, strategy: BaseAttackStrategy) -> None:
    """
    Register an attack strategy.
    
    Args:
        name: Name to register the strategy under
        strategy: The strategy instance to register
    """
    ATTACK_REGISTRY[name] = strategy


def get_attack_strategy(name: str) -> BaseAttackStrategy:
    """
    Get an attack strategy by name.
    
    Args:
        name: Name of the strategy to retrieve
        
    Returns:
        The attack strategy instance
        
    Raises:
        KeyError: If strategy not found
    """
    if name not in ATTACK_REGISTRY:
        raise KeyError(f"Attack strategy '{name}' not found in registry")
    return ATTACK_REGISTRY[name]


def list_attack_strategies() -> list[str]:
    """
    List all registered attack strategies.
    
    Returns:
        List of strategy names
    """
    return list(ATTACK_REGISTRY.keys())


def initialize_registry() -> None:
    """
    Initialize the attack strategy registry with all default strategies.
    
    This should be called at application startup.
    """
    # Register all default attack strategies
    register_attack_strategy("jailbreak", JailbreakAttack())
    register_attack_strategy("injection", InjectionAttack())
    register_attack_strategy("bias_trigger", BiasTriggerAttack())
    register_attack_strategy("context_poison", ContextPoisoningAttack())
    register_attack_strategy("role_confusion", RoleConfusionAttack())
    register_attack_strategy("chaining", ChainingAttack())


# Initialize registry on module import
initialize_registry()


__all__ = [
    "ATTACK_REGISTRY",
    "register_attack_strategy",
    "get_attack_strategy",
    "list_attack_strategies",
    "initialize_registry",
    "BaseAttackStrategy",
]
