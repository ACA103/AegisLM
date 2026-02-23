"""
Strategy Evolution Engine

Tracks attack performance history and evolves attack strategies over time.
Implements:
- Rolling vulnerability updates with exponential smoothing
- Attack performance history tracking
- Strategy evolution based on recent results

V_a^{new} = λ * V_a^{old} + (1 - λ) * V_a^{recent}
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

from adaptive.schemas import (
    AdaptiveConfig,
    AttackHistoryEntry,
    AttackVulnerability,
)
from backend.logging.logger import get_logger


class StrategyEvolution:
    """
    Manages the evolution of attack strategies over time.
    
    Uses exponential smoothing to update vulnerability scores:
    V_a^{new} = λ * V_a^{old} + (1 - λ) * V_a^{recent}
    
    Where:
    - λ (lambda) is the smoothing factor from config
    - V_a^{old} is the historical vulnerability score
    - V_a^{recent} is the vulnerability from recent evaluations
    """
    
    def __init__(
        self,
        config: Optional[AdaptiveConfig] = None,
    ):
        """
        Initialize the strategy evolution engine.
        
        Args:
            config: Adaptive configuration (uses defaults if not provided)
        """
        self.logger = get_logger(__name__)
        self._config = config or AdaptiveConfig()
        
        # Smoothing factor (lambda)
        self._lambda = self._config.evolution_smoothing
        
        # Store attack performance history
        self._attack_history: Dict[str, List[AttackHistoryEntry]] = {}
        
        # Store evolved vulnerability scores
        self._evolved_vulnerabilities: Dict[str, float] = {}
        
        # Configuration hash for reproducibility
        self._config_hash = self._compute_config_hash()
    
    @property
    def config(self) -> AdaptiveConfig:
        """Get the adaptive configuration."""
        return self._config
    
    @property
    def config_hash(self) -> str:
        """Get configuration hash for reproducibility."""
        return self._config_hash
    
    @property
    def evolved_vulnerabilities(self) -> Dict[str, float]:
        """Get evolved vulnerability scores."""
        return self._evolved_vulnerabilities.copy()
    
    def _compute_config_hash(self) -> str:
        """Compute hash of configuration for reproducibility."""
        config_dict = {
            "smoothing": self._lambda,
            "base_mutation_depth": self._config.base_mutation_depth,
            "max_mutation_depth": self._config.max_mutation_depth,
            "entropy_regularization": self._config.entropy_regularization,
        }
        sorted_config = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(sorted_config.encode()).hexdigest()
    
    def add_evaluation(
        self,
        attack_type: str,
        baseline_metrics: Dict[str, float],
        adversarial_metrics: Dict[str, float],
        model_name: str = "unknown",
        dataset_name: str = "unknown",
    ) -> None:
        """
        Add an evaluation result to history.
        
        Args:
            attack_type: Type of attack evaluated
            baseline_metrics: Metrics from baseline evaluation
            adversarial_metrics: Metrics from adversarial evaluation
            model_name: Name of the model evaluated
            dataset_name: Name of the dataset used
        """
        # Compute deltas
        hallucination_delta = (
            adversarial_metrics.get("hallucination", 0.0) 
            - baseline_metrics.get("hallucination", 0.0)
        )
        toxicity_delta = (
            adversarial_metrics.get("toxicity", 0.0) 
            - baseline_metrics.get("toxicity", 0.0)
        )
        bias_delta = (
            adversarial_metrics.get("bias", 0.0) 
            - baseline_metrics.get("bias", 0.0)
        )
        confidence_delta = (
            baseline_metrics.get("confidence", 0.5) 
            - adversarial_metrics.get("confidence", 0.5)
        )
        robustness_delta = (
            baseline_metrics.get("robustness", 0.5) 
            - adversarial_metrics.get("robustness", 0.5)
        )
        
        entry = AttackHistoryEntry(
            attack_type=attack_type,
            baseline_hallucination=baseline_metrics.get("hallucination", 0.0),
            adversarial_hallucination=adversarial_metrics.get("hallucination", 0.0),
            hallucination_delta=hallucination_delta,
            baseline_toxicity=baseline_metrics.get("toxicity", 0.0),
            adversarial_toxicity=adversarial_metrics.get("toxicity", 0.0),
            toxicity_delta=toxicity_delta,
            baseline_bias=baseline_metrics.get("bias", 0.0),
            adversarial_bias=adversarial_metrics.get("bias", 0.0),
            bias_delta=bias_delta,
            baseline_confidence=baseline_metrics.get("confidence", 0.5),
            adversarial_confidence=adversarial_metrics.get("confidence", 0.5),
            confidence_delta=confidence_delta,
            baseline_robustness=baseline_metrics.get("robustness", 0.5),
            adversarial_robustness=adversarial_metrics.get("robustness", 0.5),
            robustness_delta=robustness_delta,
            model_name=model_name,
            dataset_name=dataset_name,
            timestamp=datetime.utcnow(),
        )
        
        # Add to history
        if attack_type not in self._attack_history:
            self._attack_history[attack_type] = []
        
        self._attack_history[attack_type].append(entry)
        
        self.logger.debug(
            "Added evaluation to history",
            attack_type=attack_type,
            total_evaluations=len(self._attack_history[attack_type]),
            robustness_delta=robustness_delta,
        )
    
    def compute_recent_vulnerability(
        self,
        attack_type: str,
        window_size: Optional[int] = None,
    ) -> float:
        """
        Compute vulnerability from recent evaluations for an attack type.
        
        Args:
            attack_type: Type of attack
            window_size: Number of recent evaluations to consider
            
        Returns:
            Vulnerability score from recent evaluations
        """
        if attack_type not in self._attack_history:
            return 0.0
        
        history = self._attack_history[attack_type]
        
        if not history:
            return 0.0
        
        # Apply window if specified
        if window_size:
            history = history[-window_size:]
        
        n = len(history)
        
        # Compute mean robustness drop (higher = more vulnerable)
        mean_robustness_drop = sum(e.robustness_delta for e in history) / n
        
        # Also consider individual metric deltas
        mean_hallucination = sum(abs(e.hallucination_delta) for e in history) / n
        mean_toxicity = sum(abs(e.toxicity_delta) for e in history) / n
        mean_bias = sum(abs(e.bias_delta) for e in history) / n
        
        # Weighted combination
        # Higher hallucination, toxicity, bias = higher vulnerability
        # Higher robustness drop = higher vulnerability
        recent_vulnerability = (
            0.3 * mean_robustness_drop
            + 0.3 * mean_hallucination
            + 0.25 * mean_toxicity
            + 0.15 * mean_bias
        )
        
        # Normalize to [0, 1]
        return max(0.0, min(1.0, recent_vulnerability))
    
    def evolve_vulnerabilities(
        self,
        window_size: Optional[int] = None,
    ) -> Dict[str, float]:
        """
        Evolve vulnerability scores using exponential smoothing.
        
        V_a^{new} = λ * V_a^{old} + (1 - λ) * V_a^{recent}
        
        Args:
            window_size: Window for recent vulnerability computation
            
        Returns:
            Dictionary of evolved vulnerability scores
        """
        # Get all attack types that have history
        attack_types = list(self._attack_history.keys())
        
        if not attack_types:
            self.logger.warning("No attack history available for evolution")
            return {}
        
        evolved = {}
        
        for attack_type in attack_types:
            # Compute recent vulnerability
            recent_vuln = self._compute_recent_vulnerability(
                attack_type, 
                window_size
            )
            
            # Get old vulnerability (or 0 if not exists)
            old_vuln = self._evolved_vulnerabilities.get(attack_type, 0.0)
            
            # Apply exponential smoothing
            new_vuln = self._lambda * old_vuln + (1 - self._lambda) * recent_vuln
            
            evolved[attack_type] = new_vuln
            self._evolved_vulnerabilities[attack_type] = new_vuln
            
            self.logger.info(
                "Evolved vulnerability score",
                attack_type=attack_type,
                old_vulnerability=old_vuln,
                recent_vulnerability=recent_vuln,
                new_vulnerability=new_vuln,
                smoothing_lambda=self._lambda,
            )
        
        return evolved
    
    def get_vulnerability(
        self,
        attack_type: str,
    ) -> Optional[float]:
        """
        Get the evolved vulnerability score for an attack type.
        
        Args:
            attack_type: Type of attack
            
        Returns:
            Evolved vulnerability score if available
        """
        return self._evolved_vulnerabilities.get(attack_type)
    
    def get_attack_history(
        self,
        attack_type: Optional[str] = None,
    ) -> Dict[str, List[AttackHistoryEntry]]:
        """
        Get attack performance history.
        
        Args:
            attack_type: Optional filter by attack type
            
        Returns:
            Dictionary of attack_type -> list of history entries
        """
        if attack_type:
            return {attack_type: self._attack_history.get(attack_type, [])}
        return self._attack_history.copy()
    
    def get_statistics(self) -> Dict:
        """
        Get evolution statistics.
        
        Returns:
            Dictionary with statistics
        """
        total_evaluations = sum(
            len(entries) 
            for entries in self._attack_history.values()
        )
        
        return {
            "total_evaluations": total_evaluations,
            "unique_attack_types": len(self._attack_history),
            "attack_types": list(self._attack_history.keys()),
            "evolved_vulnerabilities": self._evolved_vulnerabilities.copy(),
            "smoothing_lambda": self._lambda,
            "config_hash": self._config_hash,
        }
    
    def clear_history(self) -> None:
        """Clear all history and evolved vulnerabilities."""
        self._attack_history.clear()
        self._evolved_vulnerabilities.clear()
        self.logger.info("Cleared strategy evolution history")
    
    def reset(self) -> None:
        """Reset the evolution engine."""
        self.clear_history()
        self._config_hash = self._compute_config_hash()


# Global evolution instance
_evolution: Optional[StrategyEvolution] = None


def get_strategy_evolution(
    config: Optional[AdaptiveConfig] = None,
) -> StrategyEvolution:
    """
    Get the global strategy evolution instance.
    
    Args:
        config: Optional adaptive configuration
        
    Returns:
        StrategyEvolution singleton
    """
    global _evolution
    if _evolution is None:
        _evolution = StrategyEvolution(config=config)
    return _evolution


def reset_strategy_evolution() -> None:
    """Reset the global strategy evolution."""
    global _evolution
    _evolution = None


__all__ = [
    "StrategyEvolution",
    "get_strategy_evolution",
    "reset_strategy_evolution",
]
