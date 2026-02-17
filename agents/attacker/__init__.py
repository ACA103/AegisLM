"""
Attacker Agent

Multi-agent adversarial LLM evaluation framework - Attacker module.

This module provides:
- AttackRequest and AttackResponse schemas
- Base attack strategy classes
- Attack engine with chaining, temperature variation, and diversity scoring
- Strategy registry for extensible attacks
- Multiple attack strategies (jailbreak, injection, bias_trigger, etc.)
"""

from agents.attacker.base import (
    BaseAttackStrategy,
    BiasTriggerStrategy,
    ChainingStrategy,
    ContextPoisoningStrategy,
    JailbreakStrategy,
    PromptInjectionStrategy,
    RoleConfusionStrategy,
)
from agents.attacker.engine import AttackEngine, get_attack_engine
from agents.attacker.registry import (
    ATTACK_REGISTRY,
    get_attack_strategy,
    initialize_registry,
    list_attack_strategies,
    register_attack_strategy,
)
from agents.attacker.schemas import AttackLog, AttackRequest, AttackResponse

__version__ = "0.1.0"

__all__ = [
    # Schemas
    "AttackRequest",
    "AttackResponse",
    "AttackLog",
    # Base strategies
    "BaseAttackStrategy",
    "PromptInjectionStrategy",
    "JailbreakStrategy",
    "BiasTriggerStrategy",
    "ContextPoisoningStrategy",
    "RoleConfusionStrategy",
    "ChainingStrategy",
    # Engine
    "AttackEngine",
    "get_attack_engine",
    # Registry
    "ATTACK_REGISTRY",
    "register_attack_strategy",
    "get_attack_strategy",
    "list_attack_strategies",
    "initialize_registry",
]
