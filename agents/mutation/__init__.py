"""
Mutation Agent Module

Prompt Mutation Engine for adversarial prompt transformation.

Exports:
- MutationEngine: Main engine for prompt mutation
- MutationRequest, MutationResponse: Request/Response schemas
- get_mutation_engine: Get global engine instance
"""

from agents.mutation.diversity import DiversityScorer, get_diversity_scorer
from agents.mutation.engine import MutationEngine, get_mutation_engine, DEFAULT_STRATEGIES
from agents.mutation.registry import (
    get_mutation_strategy,
    list_mutation_strategies,
    get_default_strategies,
    register_mutation_strategy,
    create_strategy_from_config,
)
from agents.mutation.schemas import (
    MutationLog,
    MutationRequest,
    MutationResponse,
    MutationStrategyConfig,
)

# Import strategies for direct access
from agents.mutation.strategies.synonym import SynonymStrategy
from agents.mutation.strategies.paraphrase import ParaphraseStrategy
from agents.mutation.strategies.role_swap import RoleSwapStrategy
from agents.mutation.strategies.context_obfuscation import ContextObfuscationStrategy
from agents.mutation.strategies.multi_hop import MultiHopStrategy

__all__ = [
    # Engine
    "MutationEngine",
    "get_mutation_engine",
    "DEFAULT_STRATEGIES",
    # Diversity
    "DiversityScorer",
    "get_diversity_scorer",
    # Registry
    "get_mutation_strategy",
    "list_mutation_strategies",
    "get_default_strategies",
    "register_mutation_strategy",
    "create_strategy_from_config",
    # Schemas
    "MutationLog",
    "MutationRequest",
    "MutationResponse",
    "MutationStrategyConfig",
    # Strategies
    "SynonymStrategy",
    "ParaphraseStrategy",
    "RoleSwapStrategy",
    "ContextObfuscationStrategy",
    "MultiHopStrategy",
]
