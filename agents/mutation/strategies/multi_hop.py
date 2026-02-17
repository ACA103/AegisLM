"""
Multi-Hop Mutation Strategy

Applies iterative transformations using multiple strategies
in sequence to create more complex mutations.
"""

import random
from typing import Any, Optional

from agents.mutation.strategies.synonym import SynonymStrategy
from agents.mutation.strategies.paraphrase import ParaphraseStrategy
from agents.mutation.strategies.role_swap import RoleSwapStrategy
from agents.mutation.strategies.context_obfuscation import ContextObfuscationStrategy


# Strategy weights for selection
STRATEGY_WEIGHTS = {
    "synonym": 0.25,
    "paraphrase": 0.25,
    "role_swap": 0.25,
    "context_obfuscation": 0.25,
}


class MultiHopStrategy:
    """
    Multi-hop mutation strategy.
    
    Applies multiple mutation strategies in sequence to create
    more complex and diverse adversarial prompts.
    """
    
    def __init__(
        self,
        hop_depth: int = 2,
        strategy_weights: Optional[dict[str, float]] = None,
        allow_repeat: bool = False
    ):
        """
        Initialize the multi-hop strategy.
        
        Args:
            hop_depth: Number of mutation hops (1-3)
            strategy_weights: Weights for strategy selection
            allow_repeat: Whether to allow the same strategy twice
        """
        self.hop_depth = min(max(hop_depth, 1), 3)  # Clamp to 1-3
        self.strategy_weights = strategy_weights or STRATEGY_WEIGHTS
        self.allow_repeat = allow_repeat
        
        # Initialize strategies
        self._strategies = {
            "synonym": SynonymStrategy(probability=0.3),
            "paraphrase": ParaphraseStrategy(intensity=0.5),
            "role_swap": RoleSwapStrategy(probability=0.5),
            "context_obfuscation": ContextObfuscationStrategy(probability=0.4),
        }
    
    @property
    def name(self) -> str:
        return "multi_hop"
    
    @property
    def description(self) -> str:
        return "Apply iterative transformation chains"
    
    def _select_strategy(
        self,
        available_strategies: list[str],
        seed: Optional[int] = None
    ) -> str:
        """
        Select a strategy based on weights.
        
        Args:
            available_strategies: List of strategy names to choose from
            seed: Random seed
            
        Returns:
            Selected strategy name
        """
        if seed is not None:
            random.seed(seed)
        
        # Filter by available strategies and weights
        weights = [self.strategy_weights.get(s, 0.1) for s in available_strategies]
        
        # Normalize weights
        total = sum(weights)
        if total == 0:
            return random.choice(available_strategies)
        
        probabilities = [w / total for w in weights]
        
        # Select based on probabilities
        return random.choices(available_strategies, weights=probabilities, k=1)[0]
    
    def _get_strategy_names(self) -> list[str]:
        """Get list of available strategy names."""
        return list(self._strategies.keys())
    
    def apply(self, prompt: str, seed: Optional[int] = None) -> str:
        """
        Apply multi-hop mutation to a prompt.
        
        Args:
            prompt: The prompt to mutate
            seed: Random seed for reproducibility
            
        Returns:
            Mutated prompt
        """
        if seed is not None:
            random.seed(seed)
        
        current_prompt = prompt
        selected_strategies = self._get_strategy_names()
        
        for hop in range(self.hop_depth):
            # Use different seed for each hop
            hop_seed = None
            if seed is not None:
                hop_seed = seed + hop * 100
            
            # Select a strategy
            strategy_name = self._select_strategy(selected_strategies, hop_seed)
            
            # Apply the strategy
            strategy = self._strategies[strategy_name]
            current_prompt = strategy.apply(current_prompt, hop_seed)
            
            # Update available strategies for next hop
            if not self.allow_repeat:
                selected_strategies = [s for s in selected_strategies if s != strategy_name]
                if not selected_strategies:
                    selected_strategies = self._get_strategy_names()
        
        return current_prompt
    
    def apply_with_trace(
        self,
        prompt: str,
        seed: Optional[int] = None
    ) -> tuple[str, list[str]]:
        """
        Apply multi-hop mutation and return the trace.
        
        Args:
            prompt: The prompt to mutate
            seed: Random seed for reproducibility
            
        Returns:
            Tuple of (mutated_prompt, strategy_trace)
        """
        if seed is not None:
            random.seed(seed)
        
        current_prompt = prompt
        trace = []
        selected_strategies = self._get_strategy_names()
        
        for hop in range(self.hop_depth):
            hop_seed = None
            if seed is not None:
                hop_seed = seed + hop * 100
            
            strategy_name = self._select_strategy(selected_strategies, hop_seed)
            trace.append(strategy_name)
            
            strategy = self._strategies[strategy_name]
            current_prompt = strategy.apply(current_prompt, hop_seed)
            
            if not self.allow_repeat:
                selected_strategies = [s for s in selected_strategies if s != strategy_name]
                if not selected_strategies:
                    selected_strategies = self._get_strategy_names()
        
        return current_prompt, trace


def create_multi_hop_strategy(**kwargs) -> MultiHopStrategy:
    """Factory function to create a multi-hop strategy."""
    return MultiHopStrategy(**kwargs)


__all__ = [
    "MultiHopStrategy",
    "create_multi_hop_strategy",
    "STRATEGY_WEIGHTS",
]
