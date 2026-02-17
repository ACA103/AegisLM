"""
AegisLM Dashboard Package

Governance-grade analytics interface for evaluation results,
benchmark comparisons, and model robustness visualization.
"""

__version__ = "0.1.0"

from dashboard.data_loader import DashboardDataLoader
from dashboard.schemas import (
    ComparisonData,
    DeltaRobustnessData,
    HeatmapData,
    MetricSummary,
    RadarData,
    RunMetadata,
    RunSummary,
)

__all__ = [
    "DashboardDataLoader",
    "RadarData",
    "HeatmapData",
    "DeltaRobustnessData",
    "MetricSummary",
    "RunSummary",
    "RunMetadata",
    "ComparisonData",
]
