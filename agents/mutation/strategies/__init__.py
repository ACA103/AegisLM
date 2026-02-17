"""
Mutation Strategies

Base classes and interfaces for prompt mutation strategies.
"""

from agents.mutation.strategies.synonym import SynonymStrategy
from agents.mutation.strategies.paraphrase import ParaphraseStrategy
from agents.mutation.strategies.role_swap import RoleSwapStrategy
from agents.mutation.strategies.context_obfuscation import ContextObfuscationStrategy
from agents.mutation.strategies.multi_hop import MultiHopStrategy


class MutationStrategy:
    """Base class for mutation strategies (for reference)."""
    
    @property
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    def description(self) -> str:
        raise NotImplementedError
    
    def apply(self, prompt: str, seed: int = None) -> str:
        raise NotImplementedError


__all__ = [
    "MutationStrategy",
    "SynonymStrategy",
    "ParaphraseStrategy",
    "RoleSwapStrategy",
    "ContextObfuscationStrategy",
    "MultiHopStrategy",
]
