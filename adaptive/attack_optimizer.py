"""
Attack Optimizer

Optimizes attack selection probabilities based on vulnerability scores.
Implements:
- Probability proportional to vulnerability: P(a) = V_a / ΣV_a
- Entropy regularization to maintain diversity
- Mutation depth optimization based on vulnerability
"""

import math
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from adaptive.schemas import (
    AdaptiveConfig,
    AdaptiveSelectionProbabilities,
    VulnerabilityWeights,
)
from backend.logging.logger import get_logger


class AttackOptimizer:
    """
    Optimizes attack selection for adaptive evaluation.
    
    Key features:
    - Vulnerability-based probability weighting
    - Entropy regularization for diversity
    - Mutation depth optimization
    """
    
    def __init__(
        self,
        config: Optional[AdaptiveConfig] = None,
    ):
        """
        Initialize the attack optimizer.
        
        Args:
            config: Adaptive configuration (uses defaults if not provided)
        """
        self.logger = get_logger(__name__)
        self._config = config or AdaptiveConfig()
        
        # Store current selection probabilities
        self._current_probabilities: Dict[str, float] = {}
        self._current_mutation_depths: Dict[str, int] = {}
        
        # Track iterations
        self._iteration_count = 0
    
    @property
    def config(self) -> AdaptiveConfig:
        """Get the adaptive configuration."""
        return self._config
    
    @property
    def current_probabilities(self) -> Dict[str, float]:
        """Get current attack selection probabilities."""
        return self._current_probabilities.copy()
    
    @property
    def current_mutation_depths(self) -> Dict[str, int]:
        """Get current mutation depths per attack type."""
        return self._current_mutation_depths.copy()
    
    def compute_probabilities(
        self,
        vulnerabilities: Dict[str, float],
        attack_types: Optional[List[str]] = None,
    ) -> AdaptiveSelectionProbabilities:
        """
        Compute attack selection probabilities from vulnerability scores.
        
        Uses vulnerability-proportional selection with entropy regularization:
        P(a) = (1 - ε) * (V_a / ΣV_a) + ε * (1/|A|)
        
        Args:
            vulnerabilities: Dictionary of attack_type -> vulnerability score
            attack_types: Optional list of attack types to include
            
        Returns:
            AdaptiveSelectionProbabilities with computed probabilities
        """
        self._iteration_count += 1
        iteration = self._iteration_count
        
        # Get all attack types to consider
        if attack_types is None:
            attack_types = list(vulnerabilities.keys())
        
        if not attack_types:
            self.logger.warning("No attack types provided for probability computation")
            return AdaptiveSelectionProbabilities(
                iteration=iteration,
                probabilities={},
                mutation_depths={},
                entropy=0.0,
                timestamp=datetime.utcnow(),
            )
        
        # Compute raw probabilities (proportional to vulnerability)
        total_vulnerability = sum(
            vulnerabilities.get(at, 0.0) 
            for at in attack_types
        )
        
        if total_vulnerability <= 0:
            # Equal distribution if no vulnerabilities
            raw_probs = {at: 1.0 / len(attack_types) for at in attack_types}
            self.logger.warning(
                "No vulnerability scores available, using uniform distribution"
            )
        else:
            # Proportional to vulnerability
            raw_probs = {
                at: vulnerabilities.get(at, 0.0) / total_vulnerability
                for at in attack_types
            }
        
        # Apply entropy regularization
        epsilon = self._config.entropy_regularization
        uniform_prob = 1.0 / len(attack_types)
        
        probabilities = {
            at: (1 - epsilon) * raw_probs.get(at, 0.0) + epsilon * uniform_prob
            for at in attack_types
        }
        
        # Normalize to ensure they sum to 1
        total = sum(probabilities.values())
        if total > 0:
            probabilities = {at: p / total for at, p in probabilities.items()}
        
        # Compute entropy
        entropy = self._compute_entropy(probabilities)
        
        # Compute mutation depths
        mutation_depths = self._compute_mutation_depths(vulnerabilities)
        
        result = AdaptiveSelectionProbabilities(
            iteration=iteration,
            probabilities=probabilities,
            mutation_depths=mutation_depths,
            entropy=entropy,
            timestamp=datetime.utcnow(),
        )
        
        # Store current state
        self._current_probabilities = probabilities
        self._current_mutation_depths = mutation_depths
        
        self.logger.info(
            "Computed adaptive attack probabilities",
            iteration=iteration,
            entropy=entropy,
            num_attack_types=len(attack_types),
        )
        
        return result
    
    def _compute_entropy(self, probabilities: Dict[str, float]) -> float:
        """
        Compute entropy of probability distribution.
        
        H = -Σ P(a) * log(P(a))
        
        Args:
            probabilities: Dictionary of probabilities
            
        Returns:
            Entropy value
        """
        entropy = 0.0
        for p in probabilities.values():
            if p > 0:
                entropy -= p * math.log(p)
        return entropy
    
    def _compute_mutation_depths(
        self,
        vulnerabilities: Dict[str, float],
    ) -> Dict[str, int]:
        """
        Compute mutation depth for each attack type based on vulnerability.
        
        Higher vulnerability -> higher mutation depth:
        depth = base_depth + 1 if vulnerability > threshold
        
        Args:
            vulnerabilities: Dictionary of vulnerability scores
            
        Returns:
            Dictionary of attack_type -> mutation depth
        """
        base_depth = self._config.base_mutation_depth
        max_depth = self._config.max_mutation_depth
        
        # Compute threshold (e.g., top 25% vulnerability)
        if vulnerabilities:
            sorted_vulns = sorted(vulnerabilities.values(), reverse=True)
            threshold_idx = max(0, len(sorted_vulns) // 4)
            threshold = sorted_vulns[threshold_idx] if sorted_vulns else 0.5
        else:
            threshold = 0.5
        
        mutation_depths = {}
        for attack_type, vuln in vulnerabilities.items():
            if vuln >= threshold:
                # High vulnerability: increase depth
                mutation_depths[attack_type] = min(base_depth + 1, max_depth)
            else:
                # Normal depth for lower vulnerability
                mutation_depths[attack_type] = base_depth
        
        return mutation_depths
    
    def select_attack(
        self,
        probabilities: Optional[Dict[str, float]] = None,
    ) -> str:
        """
        Select an attack type based on probabilities.
        
        Args:
            probabilities: Optional probability distribution to use
            
        Returns:
            Selected attack type
        """
        if probabilities is None:
            probabilities = self._current_probabilities
        
        if not probabilities:
            self.logger.warning("No probabilities available, defaulting to random")
            return "jailbreak"  # Default attack type
        
        # Weighted random selection
        attack_types = list(probabilities.keys())
        weights = list(probabilities.values())
        
        selected = random.choices(attack_types, weights=weights, k=1)[0]
        
        self.logger.debug(
            "Selected attack",
            attack_type=selected,
            probability=probabilities[selected],
        )
        
        return selected
    
    def get_mutation_depth(
        self,
        attack_type: str,
    ) -> int:
        """
        Get the mutation depth for a specific attack type.
        
        Args:
            attack_type: Type of attack
            
        Returns:
            Mutation depth
        """
        return self._current_mutation_depths.get(
            attack_type, 
            self._config.base_mutation_depth,
        )
    
    def reset(self) -> None:
        """Reset the optimizer state."""
        self._current_probabilities = {}
        self._current_mutation_depths = {}
        self._iteration_count = 0
        self.logger.info("Reset attack optimizer")


# Global optimizer instance
_optimizer: Optional[AttackOptimizer] = None


def get_attack_optimizer(
    config: Optional[AdaptiveConfig] = None,
) -> AttackOptimizer:
    """
    Get the global attack optimizer instance.
    
    Args:
        config: Optional adaptive configuration
        
    Returns:
        AttackOptimizer singleton
    """
    global _optimizer
    if _optimizer is None:
        _optimizer = AttackOptimizer(config=config)
    return _optimizer


def reset_attack_optimizer() -> None:
    """Reset the global attack optimizer."""
    global _optimizer
    _optimizer = None


__all__ = [
    "AttackOptimizer",
    "get_attack_optimizer",
    "reset_attack_optimizer",
]
