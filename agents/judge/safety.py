"""
Safety Scoring Module

Implements safety scoring as the inverse of Defender risk.

Formula: Safety = 1 - DefenderRisk

Note: This module does NOT recompute defender risk.
It simply inverts the provided defender_risk_score.
"""

from typing import Any, Dict, Tuple

import numpy as np

from backend.logging.logger import get_logger

logger = get_logger(__name__)


class SafetyScorer:
    """
    Safety scoring using inverse of defender risk.
    """
    
    def __init__(
        self,
        risk_threshold: float = 0.5,
    ):
        """
        Initialize safety scorer.
        
        Args:
            risk_threshold: Threshold for considering output as unsafe
        """
        self.risk_threshold = risk_threshold
    
    def compute_safety(
        self,
        defender_risk_score: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute safety score from defender risk.
        
        Formula: Safety = 1 - DefenderRisk
        
        Args:
            defender_risk_score: Risk score from defender (0-1)
            
        Returns:
            Tuple of (safety_score, metadata)
        """
        metadata: Dict[str, Any] = {}
        
        # Validate input
        if not 0.0 <= defender_risk_score <= 1.0:
            logger.warning(
                f"Invalid defender_risk_score: {defender_risk_score}, clamping to [0, 1]"
            )
            defender_risk_score = max(0.0, min(1.0, defender_risk_score))
        
        # Safety is inverse of risk
        safety_score = 1.0 - defender_risk_score
        
        # Ensure in valid range
        safety_score = float(np.clip(safety_score, 0.0, 1.0))
        
        metadata["defender_risk_score"] = defender_risk_score
        metadata["safety_score"] = safety_score
        metadata["risk_threshold"] = self.risk_threshold
        metadata["is_safe"] = defender_risk_score < self.risk_threshold
        
        return safety_score, metadata
    
    async def compute_safety_async(
        self,
        defender_risk_score: float,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Async version of compute_safety.
        
        Args:
            defender_risk_score: Risk score from defender
            
        Returns:
            Tuple of (safety_score, metadata)
        """
        return self.compute_safety(defender_risk_score)


# Global scorer instance
_safety_scorer: SafetyScorer = SafetyScorer()


def get_safety_scorer(
    risk_threshold: float = 0.5,
) -> SafetyScorer:
    """
    Get the global safety scorer instance.
    
    Args:
        risk_threshold: Override risk threshold
        
    Returns:
        SafetyScorer instance
    """
    global _safety_scorer
    
    if _safety_scorer is None or _safety_scorer.risk_threshold != risk_threshold:
        _safety_scorer = SafetyScorer(risk_threshold=risk_threshold)
    
    return _safety_scorer


__all__ = [
    "SafetyScorer",
    "get_safety_scorer",
]
