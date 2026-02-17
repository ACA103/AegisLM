"""
Scoring Module

Composite score calculation and aggregation.
"""

from backend.scoring.aggregator import (
    ScoreAggregator,
    ScoreWeights,
    MetricScores,
    AggregatedScores,
    get_aggregator,
    calculate_robustness,
)

__all__ = [
    "ScoreAggregator",
    "ScoreWeights",
    "MetricScores",
    "AggregatedScores",
    "get_aggregator",
    "calculate_robustness",
]
