"""
Benchmarking module init workaround.

This file provides an alternative import path for the benchmarking module.
Import as: from backend.benchmarking_init import BenchmarkEngine
"""

# Import all key classes from the benchmarking module
from backend.benchmarking.engine import BenchmarkEngine, get_benchmark_engine, BenchmarkEvent
from backend.benchmarking.schemas import (
    BenchmarkConfig,
    BenchmarkMode, 
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkWeights,
    StartBenchmarkRequest,
)
from backend.benchmarking.statistics import (
    calculate_mean,
    calculate_standard_deviation,
    paired_t_test,
)
from backend.benchmarking.comparison import rank_models, compare_models
from backend.benchmarking.reporter import generate_benchmark_artifact, generate_text_report

__all__ = [
    "BenchmarkEngine",
    "get_benchmark_engine", 
    "BenchmarkEvent",
    "BenchmarkConfig",
    "BenchmarkMode",
    "BenchmarkResult",
    "BenchmarkStatus", 
    "BenchmarkWeights",
    "StartBenchmarkRequest",
    "calculate_mean",
    "calculate_standard_deviation",
    "paired_t_test",
    "rank_models",
    "compare_models",
    "generate_benchmark_artifact",
    "generate_text_report",
]
