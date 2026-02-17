"""
Defender Agent

Multi-agent adversarial LLM evaluation framework - Defender module.

This module provides:
- DefenderRequest and DefenderResponse schemas
- Hybrid rule-based + model-based detection
- Injection detection
- Role override detection
- Toxicity classification
- Semantic policy checking
- Risk score computation
"""

from agents.defender.base import (
    BaseDefenseStrategy,
    InjectionDefenseStrategy,
    RoleOverrideDefenseStrategy,
    ToxicityDefenseStrategy,
    SemanticPolicyDefenseStrategy,
)
from agents.defender.engine import (
    DefenderEngine,
    get_defender_engine,
)
from agents.defender.registry import (
    DEFENSE_REGISTRY,
    DefenseStrategy,
    DefaultDefenseStrategy,
    PromptSanitizationStrategy,
    OutputFilteringStrategy,
    get_defense_strategy,
    initialize_registry,
    list_defense_strategies,
    register_defense_strategy,
)
from agents.defender.schemas import (
    DefenderConfig,
    DefenderLog,
    DefenderRequest,
    DefenderResponse,
)

__version__ = "0.1.0"

__all__ = [
    # Base
    "BaseDefenseStrategy",
    "InjectionDefenseStrategy",
    "RoleOverrideDefenseStrategy",
    "ToxicityDefenseStrategy",
    "SemanticPolicyDefenseStrategy",
    # Engine
    "DefenderEngine",
    "get_defender_engine",
    # Schemas
    "DefenderRequest",
    "DefenderResponse",
    "DefenderLog",
    "DefenderConfig",
    # Registry
    "DEFENSE_REGISTRY",
    "DefenseStrategy",
    "DefaultDefenseStrategy",
    "PromptSanitizationStrategy",
    "OutputFilteringStrategy",
    "get_defense_strategy",
    "list_defense_strategies",
    "register_defense_strategy",
    "initialize_registry",
]
