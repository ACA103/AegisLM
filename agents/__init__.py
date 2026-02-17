"""
AegisLM Agents Package

Multi-agent adversarial LLM evaluation framework.

This package contains:
- Attacker agent: Generates adversarial prompts
- Defender agent: Detects and blocks malicious inputs/outputs
- Judge agent: Evaluates model robustness
- Mutation agent: Mutates prompts for diversity
"""

from agents.attacker import (
    AttackEngine,
    AttackRequest,
    AttackResponse,
    AttackLog,
    BaseAttackStrategy,
    PromptInjectionStrategy,
    JailbreakStrategy,
    BiasTriggerStrategy,
    ContextPoisoningStrategy,
    RoleConfusionStrategy,
    ChainingStrategy,
    get_attack_engine,
    ATTACK_REGISTRY,
    get_attack_strategy,
    list_attack_strategies,
    register_attack_strategy,
    initialize_registry,
)

from agents.defender import (
    BaseDefenseStrategy,
    InjectionDefenseStrategy,
    RoleOverrideDefenseStrategy,
    ToxicityDefenseStrategy,
    SemanticPolicyDefenseStrategy,
    DefenderEngine,
    DefenderRequest,
    DefenderResponse,
    DefenderLog,
    DefenderConfig,
    get_defender_engine,
    DEFENSE_REGISTRY,
    DefenseStrategy,
    DefaultDefenseStrategy,
    PromptSanitizationStrategy,
    OutputFilteringStrategy,
    get_defense_strategy,
    list_defense_strategies,
    register_defense_strategy,
    initialize_registry as init_defense_registry,
)

__version__ = "0.1.0"

__all__ = [
    # Attacker
    "AttackEngine",
    "AttackRequest",
    "AttackResponse",
    "AttackLog",
    "BaseAttackStrategy",
    "PromptInjectionStrategy",
    "JailbreakStrategy",
    "BiasTriggerStrategy",
    "ContextPoisoningStrategy",
    "RoleConfusionStrategy",
    "ChainingStrategy",
    "get_attack_engine",
    "ATTACK_REGISTRY",
    "get_attack_strategy",
    "list_attack_strategies",
    "register_attack_strategy",
    "initialize_registry",
    # Defender Base
    "BaseDefenseStrategy",
    "InjectionDefenseStrategy",
    "RoleOverrideDefenseStrategy",
    "ToxicityDefenseStrategy",
    "SemanticPolicyDefenseStrategy",
    # Defender
    "DefenderEngine",
    "DefenderRequest",
    "DefenderResponse",
    "DefenderLog",
    "DefenderConfig",
    "get_defender_engine",
    "DEFENSE_REGISTRY",
    "DefenseStrategy",
    "DefaultDefenseStrategy",
    "PromptSanitizationStrategy",
    "OutputFilteringStrategy",
    "get_defense_strategy",
    "list_defense_strategies",
    "register_defense_strategy",
    "init_defense_registry",
]
