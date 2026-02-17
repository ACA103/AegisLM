"""
Judge Utility Functions

Helper functions for the Judge agent.
"""

from typing import Any, Dict, List, Optional
import numpy as np


def clamp_score(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Clamp a score to the specified range.
    
    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value
        
    Returns:
        Clamped value
    """
    return float(np.clip(value, min_val, max_val))


def calculate_weighted_score(
    score: float,
    weight: float,
    inverse: bool = False,
) -> float:
    """
    Calculate weighted score, optionally inverting.
    
    Args:
        score: Score value
        weight: Weight to apply
        inverse: Whether to invert the score (1 - score)
        
    Returns:
        Weighted score
    """
    if inverse:
        return weight * (1.0 - score)
    return weight * score


def format_score_dict(scores: Dict[str, float]) -> Dict[str, Any]:
    """
    Format scores dictionary with normalized values.
    
    Args:
        scores: Dictionary of scores
        
    Returns:
        Formatted dictionary
    """
    formatted = {}
    for key, value in scores.items():
        formatted[key] = clamp_score(value)
    return formatted


def aggregate_scores(scores: List[float]) -> Dict[str, float]:
    """
    Aggregate a list of scores.
    
    Args:
        scores: List of score values
        
    Returns:
        Dictionary with mean and std
    """
    if not scores:
        return {"mean": 0.0, "std": 0.0, "min": 0.0, "max": 0.0}
    
    arr = np.array(scores)
    return {
        "mean": float(np.mean(arr)),
        "std": float(np.std(arr)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
    }


def validate_scores(
    hallucination: Optional[float] = None,
    safety: Optional[float] = None,
    bias: Optional[float] = None,
    confidence: Optional[float] = None,
) -> None:
    """
    Validate that all scores are in valid range [0, 1].
    
    Args:
        hallucination: Hallucination score
        safety: Safety score
        bias: Bias score
        confidence: Confidence score
        
    Raises:
        ValueError: If any score is out of range
    """
    for name, score in [
        ("hallucination", hallucination),
        ("safety", safety),
        ("bias", bias),
        ("confidence", confidence),
    ]:
        if score is not None:
            if not 0.0 <= score <= 1.0:
                raise ValueError(f"{name} score must be in [0, 1], got {score}")


__all__ = [
    "clamp_score",
    "calculate_weighted_score",
    "format_score_dict",
    "aggregate_scores",
    "validate_scores",
]
