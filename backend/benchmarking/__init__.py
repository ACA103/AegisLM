"""
AegisLM Benchmarking Module

Provides benchmarking capabilities for evaluating LLM robustness:
- Baseline evaluation mode
- Adversarial evaluation mode
- Delta robustness computation
- Cross-model comparison
- Statistical reporting
- Benchmark artifact generation
"""

from backend.benchmarking.comparison import (
    compare_models,
    find_most_robust_model,
    find_most_stable_model,
    find_most_vulnerable_model,
    generate_comparative_report,
    generate_vulnerability_heatmap,
    get_attack_type_vulnerability,
    rank_models,
)
from backend.benchmarking.engine import (
    BenchmarkEngine,
    BenchmarkEvent,
    get_benchmark_engine,
)
from backend.benchmarking.reporter import (
    DEFAULT_BENCHMARK_DIR,
    export_to_csv,
    generate_benchmark_artifact,
    generate_summary_report,
    generate_text_report,
    list_benchmarks,
    load_benchmark_artifact,
)
from backend.benchmarking.schemas import (
    BenchmarkMode,
    BenchmarkPerformance,
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkWeights,
    EvaluationResult,
    MetricDeltas,
    ModelBenchmarkResult,
    ModelMetrics,
    ModelRanking,
    StartBenchmarkRequest,
    StartBenchmarkResponse,
    VulnerabilityHeatmap,
    VulnerabilityHeatmapCell,
)
from backend.benchmarking.statistics import (
    MetricStatistics,
    calculate_confidence_interval,
    calculate_mean,
    calculate_mean_with_ci,
    calculate_paired_differences,
    calculate_standard_deviation,
    calculate_variance,
    calculate_sample_std,
    cohens_d,
    calculate_vulnerability_consistency,
    generate_summary_statistics,
    paired_t_test,
)


__all__ = [
    # Comparison
    "compare_models",
    "find_most_robust_model",
    "find_most_stable_model",
    "find_most_vulnerable_model",
    "generate_comparative_report",
    "generate_vulnerability_heatmap",
    "get_attack_type_vulnerability",
    "rank_models",
    # Engine
    "BenchmarkEngine",
    "BenchmarkEvent",
    "get_benchmark_engine",
    # Reporter
    "DEFAULT_BENCHMARK_DIR",
    "export_to_csv",
    "generate_benchmark_artifact",
    "generate_summary_report",
    "generate_text_report",
    "list_benchmarks",
    "load_benchmark_artifact",
    # Schemas
    "BenchmarkMode",
    "BenchmarkPerformance",
    "BenchmarkResult",
    "BenchmarkStatus",
    "BenchmarkWeights",
    "EvaluationResult",
    "MetricDeltas",
    "ModelBenchmarkResult",
    "ModelMetrics",
    "ModelRanking",
    "StartBenchmarkRequest",
    "StartBenchmarkResponse",
    "VulnerabilityHeatmap",
    "VulnerabilityHeatmapCell",
    # Statistics
    "MetricStatistics",
    "calculate_confidence_interval",
    "calculate_mean",
    "calculate_mean_with_ci",
    "calculate_paired_differences",
    "calculate_standard_deviation",
    "calculate_variance",
    "calculate_sample_std",
    "cohens_d",
    "calculate_vulnerability_consistency",
    "generate_summary_statistics",
    "paired_t_test",
]
