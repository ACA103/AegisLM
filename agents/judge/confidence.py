"""
Confidence Scoring Module

Implements confidence scoring using:
- Token Probability Mean: Average of token probabilities
- Entropy-Based Confidence: 1 - normalized entropy

Formula: C = gamma * C1 + (1 - gamma) * C2
Where:
- C1 = (1/n) * sum(p(token_i))
- C2 = 1 - (H_entropy / H_max)
- gamma + (1-gamma) = 1
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.logging.logger import get_logger

logger = get_logger(__name__)


class ConfidenceScorer:
    """
    Confidence scoring using token probabilities and entropy.
    """
    
    def __init__(
        self,
        gamma: float = 0.5,
    ):
        """
        Initialize confidence scorer.
        
        Args:
            gamma: Weight for token probability component (0-1)
        """
        self.gamma = gamma
        
        # Validate gamma
        if not 0.0 <= gamma <= 1.0:
            raise ValueError(f"gamma must be in [0, 1], got {gamma}")
    
    def compute_token_probability_mean(
        self,
        token_probs: List[float],
    ) -> float:
        """
        Compute mean token probability.
        
        Formula: C1 = (1/n) * sum(p(token_i))
        
        Args:
            token_probs: List of token probabilities
            
        Returns:
            Mean probability in [0, 1]
        """
        if not token_probs or len(token_probs) == 0:
            return 0.0
        
        # Clamp probabilities to valid range
        clamped_probs = [max(0.0, min(1.0, p)) for p in token_probs]
        
        # Compute mean
        mean_prob = sum(clamped_probs) / len(clamped_probs)
        
        return float(mean_prob)
    
    def compute_entropy(
        self,
        token_probs: List[float],
    ) -> float:
        """
        Compute token entropy.
        
        Formula: H_entropy = -sum(p_i * log(p_i))
        
        Uses natural log, result in range [0, log(n)]
        
        Args:
            token_probs: List of token probabilities
            
        Returns:
            Entropy value
        """
        if not token_probs or len(token_probs) == 0:
            return 0.0
        
        # Clamp probabilities to avoid log(0)
        epsilon = 1e-10
        clamped_probs = [max(epsilon, min(1.0 - epsilon, p)) for p in token_probs]
        
        # Compute entropy
        entropy = 0.0
        for p in clamped_probs:
            entropy -= p * math.log(p)
        
        return float(entropy)
    
    def compute_entropy_based_confidence(
        self,
        token_probs: List[float],
    ) -> float:
        """
        Compute entropy-based confidence.
        
        Formula: C2 = 1 - (H_entropy / H_max)
        
        Where H_max = log(n) for uniform distribution
        
        Args:
            token_probs: List of token probabilities
            
        Returns:
            Entropy-based confidence in [0, 1]
        """
        if not token_probs or len(token_probs) == 0:
            return 0.5  # Neutral confidence
        
        n = len(token_probs)
        
        # Compute entropy
        entropy = self.compute_entropy(token_probs)
        
        # Maximum entropy for n tokens (uniform distribution)
        h_max = math.log(n) if n > 0 else 1.0
        
        # Normalize entropy to [0, 1]
        if h_max > 0:
            normalized_entropy = entropy / h_max
        else:
            normalized_entropy = 0.0
        
        # Confidence is inverse of normalized entropy
        confidence = 1.0 - normalized_entropy
        
        return float(np.clip(confidence, 0.0, 1.0))
    
    async def compute_confidence(
        self,
        token_probs: Optional[List[float]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute confidence score.
        
        Formula: C = gamma * C1 + (1 - gamma) * C2
        
        Args:
            token_probs: Optional list of token probabilities from model generation
            
        Returns:
            Tuple of (confidence_score, metadata)
        """
        metadata: Dict[str, Any] = {}
        
        if token_probs is None or len(token_probs) == 0:
            # No token probabilities available - return neutral confidence
            logger.warning(
                "No token probabilities provided, returning neutral confidence"
            )
            metadata["confidence_score"] = 0.5
            metadata["method"] = "none"
            metadata["note"] = "No token probabilities available"
            return 0.5, metadata
        
        # Component 1: Token probability mean
        prob_mean = self.compute_token_probability_mean(token_probs)
        metadata["token_probability_mean"] = prob_mean
        
        # Component 2: Entropy-based confidence
        entropy_confidence = self.compute_entropy_based_confidence(token_probs)
        metadata["entropy_based_confidence"] = entropy_confidence
        
        # Raw entropy value
        raw_entropy = self.compute_entropy(token_probs)
        n_tokens = len(token_probs)
        h_max = math.log(n_tokens) if n_tokens > 0 else 1.0
        metadata["raw_entropy"] = raw_entropy
        metadata["max_entropy"] = h_max
        metadata["normalized_entropy"] = raw_entropy / h_max if h_max > 0 else 0.0
        
        # Final confidence score
        confidence_score = (
            self.gamma * prob_mean +
            (1.0 - self.gamma) * entropy_confidence
        )
        
        confidence_score = float(np.clip(confidence_score, 0.0, 1.0))
        
        metadata["confidence_score"] = confidence_score
        metadata["gamma_used"] = self.gamma
        metadata["num_tokens"] = n_tokens
        metadata["method"] = "combined"
        
        return confidence_score, metadata
    
    def compute_confidence_without_async(
        self,
        token_probs: Optional[List[float]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Synchronous version of compute_confidence.
        
        Args:
            token_probs: Optional list of token probabilities
            
        Returns:
            Tuple of (confidence_score, metadata)
        """
        metadata: Dict[str, Any] = {}
        
        if token_probs is None or len(token_probs) == 0:
            metadata["confidence_score"] = 0.5
            metadata["method"] = "none"
            return 0.5, metadata
        
        # Component 1
        prob_mean = self.compute_token_probability_mean(token_probs)
        metadata["token_probability_mean"] = prob_mean
        
        # Component 2
        entropy_confidence = self.compute_entropy_based_confidence(token_probs)
        metadata["entropy_based_confidence"] = entropy_confidence
        
        # Raw entropy
        raw_entropy = self.compute_entropy(token_probs)
        n_tokens = len(token_probs)
        h_max = math.log(n_tokens) if n_tokens > 0 else 1.0
        metadata["raw_entropy"] = raw_entropy
        metadata["max_entropy"] = h_max
        
        # Final
        confidence_score = (
            self.gamma * prob_mean +
            (1.0 - self.gamma) * entropy_confidence
        )
        
        confidence_score = float(np.clip(confidence_score, 0.0, 1.0))
        
        metadata["confidence_score"] = confidence_score
        metadata["gamma_used"] = self.gamma
        metadata["num_tokens"] = n_tokens
        metadata["method"] = "combined"
        
        return confidence_score, metadata


# Global scorer instance
_confidence_scorer: Optional[ConfidenceScorer] = None


def get_confidence_scorer(
    gamma: Optional[float] = None,
) -> ConfidenceScorer:
    """
    Get the global confidence scorer instance.
    
    Args:
        gamma: Override gamma parameter
        
    Returns:
        ConfidenceScorer instance
    """
    global _confidence_scorer
    
    if _confidence_scorer is None:
        _confidence_scorer = ConfidenceScorer(gamma=gamma if gamma is not None else 0.5)
    
    return _confidence_scorer


__all__ = [
    "ConfidenceScorer",
    "get_confidence_scorer",
]
