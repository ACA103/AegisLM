"""
Benchmarking Schemas

Data models for the AegisLM Benchmarking Engine.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# Enums
# =============================================================================

class BenchmarkMode(str, Enum):
    """Benchmark evaluation mode."""
    BASELINE = "baseline"
    ADVERSARIAL = "adversarial"
    CROSS_MODEL = "cross_model"


class BenchmarkStatus(str, Enum):
    """Status of a benchmark run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# Configuration Models
# =============================================================================

class BenchmarkWeights(BaseModel):
    """Weights for benchmark scoring."""
    hallucination: float = Field(default=0.25, ge=0.0, le=1.0)
    toxicity: float = Field(default=0.25, ge=0.0, le=1.0)
    bias: float = Field(default=0.25, ge=0.0, le=1.0)
    confidence: float = Field(default=0.25, ge=0.0, le=1.0)

    @field_validator("hallucination", "toxicity", "bias", "confidence")
    @classmethod
    def validate_weight(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be in [0, 1], got {v}")
        return v

    def validate_sum(self) -> None:
        """Validate that weights sum to 1.0."""
        total = self.hallucination + self.toxicity + self.bias + self.confidence
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Weights must sum to 1.0, got {total}")


class BenchmarkConfig(BaseModel):
    """
    Configuration for a benchmark run.
    
    This is the main entry point for starting a benchmark evaluation.
    """
    benchmark_id: UUID = Field(description="Unique benchmark identifier")
    models: List[str] = Field(description="List of model names to evaluate")
    dataset_name: str = Field(description="Dataset name")
    dataset_version: str = Field(description="Dataset version to use")
    attack_enabled: bool = Field(default=True, description="Enable attack generation")
    mutation_depth: int = Field(default=2, ge=0, le=10, description="Mutation depth")
    weights: BenchmarkWeights = Field(
        default_factory=BenchmarkWeights,
        description="Scoring weights"
    )
    max_concurrency: int = Field(default=4, ge=1, le=32)
    max_samples: Optional[int] = Field(
        default=None,
        description="Maximum samples per model (for quick benchmarking)"
    )
    enable_baseline: bool = Field(
        default=True,
        description="Run baseline evaluation (no attacks)"
    )
    enable_adversarial: bool = Field(
        default=True,
        description="Run adversarial evaluation (with attacks)"
    )
    attack_types: List[str] = Field(
        default_factory=lambda: ["jailbreak"],
        description="Attack types to use"
    )

    def validate_config(self) -> None:
        """Validate benchmark configuration."""
        self.weights.validate_sum()
        if not self.models:
            raise ValueError("At least one model must be specified")
        if not self.enable_baseline and not self.enable_adversarial:
            raise ValueError("At least one of baseline or adversarial must be enabled")


# =============================================================================
# Result Models
# =============================================================================

class ModelMetrics(BaseModel):
    """Metrics for a single model evaluation."""
    hallucination: float = Field(ge=0.0, le=1.0)
    toxicity: float = Field(ge=0.0, le=1.0)
    bias: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    robustness: float = Field(ge=0.0, le=1.0)
    
    # Standard deviations
    std_hallucination: Optional[float] = None
    std_toxicity: Optional[float] = None
    std_bias: Optional[float] = None
    std_confidence: Optional[float] = None


class MetricDeltas(BaseModel):
    """
    Delta (change) in metrics between baseline and adversarial.
    
    Positive delta means metric worsened under adversarial conditions.
    """
    hallucination_delta: float = Field(
        description="Mean hallucination change (adversarial - baseline)"
    )
    toxicity_delta: float = Field(
        description="Mean toxicity change (adversarial - baseline)"
    )
    bias_delta: float = Field(
        description="Mean bias change (adversarial - baseline)"
    )
    confidence_delta: float = Field(
        description="Mean confidence change (adversarial - baseline)"
    )
    robustness_delta: float = Field(
        description="Robustness change (baseline - adversarial)"
    )


class EvaluationResult(BaseModel):
    """Result of a single model evaluation."""
    model_name: str
    mode: BenchmarkMode
    metrics: ModelMetrics
    sample_count: int
    failure_rate: float = Field(ge=0.0, le=1.0)
    mean_latency_ms: Optional[float] = None
    total_time_seconds: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelBenchmarkResult(BaseModel):
    """
    Complete benchmark result for a single model.
    
    Contains both baseline and adversarial results, plus computed deltas.
    """
    model_name: str
    baseline: Optional[EvaluationResult] = None
    adversarial: Optional[EvaluationResult] = None
    deltas: Optional[MetricDeltas] = None
    
    # Derived metrics
    baseline_robustness: Optional[float] = None
    adversarial_robustness: Optional[float] = None
    delta_robustness: Optional[float] = None
    
    # Additional metrics
    robustness_stability_index: Optional[float] = Field(
        default=None,
        description="RSI = R_adv / R_base (closer to 1 = more stable)"
    )
    vulnerability_index: Optional[float] = Field(
        default=None,
        description="VI = delta_R / R_base (higher = more fragile)"
    )


# =============================================================================
# Ranking and Comparison
# =============================================================================

class ModelRanking(BaseModel):
    """Ranking information for a model."""
    model_name: str
    rank: int
    robustness_score: float
    hallucination_resilience: float
    bias_stability: float
    confidence_retention: float
    overall_score: float


class VulnerabilityHeatmapCell(BaseModel):
    """Single cell in the vulnerability heatmap."""
    attack_type: str
    metric: str
    value: float = Field(ge=0.0, le=1.0)
    sample_count: int


class VulnerabilityHeatmap(BaseModel):
    """Vulnerability heatmap matrix."""
    rows: List[str] = Field(description="Attack types")
    columns: List[str] = Field(description="Metrics")
    cells: List[VulnerabilityHeatmapCell]


# =============================================================================
# Benchmark Output
# =============================================================================

class BenchmarkPerformance(BaseModel):
    """Performance tracking for a benchmark."""
    time_per_model_seconds: Dict[str, float] = Field(default_factory=dict)
    gpu_memory_mb: Optional[Dict[str, float]] = None
    sample_counts: Dict[str, int] = Field(default_factory=dict)
    failure_rates: Dict[str, float] = Field(default_factory=dict)


class BenchmarkResult(BaseModel):
    """
    Complete benchmark result for multiple models.
    """
    benchmark_id: UUID
    dataset_name: str
    dataset_version: str
    models: List[str]
    status: BenchmarkStatus
    
    # Results per model
    results: List[ModelBenchmarkResult]
    
    # Rankings (if multiple models)
    rankings: Optional[List[ModelRanking]] = None
    
    # Vulnerability heatmap
    vulnerability_heatmap: Optional[VulnerabilityHeatmap] = None
    
    # Performance tracking
    performance: BenchmarkPerformance
    
    # Timestamps
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Error information
    error: Optional[str] = None
    
    # Configuration used
    config: Optional[Dict[str, Any]] = None


# =============================================================================
# API Input/Output
# =============================================================================

class StartBenchmarkRequest(BaseModel):
    """Request to start a benchmark."""
    models: List[str] = Field(description="List of model names to evaluate")
    dataset_name: str = Field(default="truthfulqa")
    dataset_version: str = Field(default="v1.0")
    attack_enabled: bool = Field(default=True)
    mutation_depth: int = Field(default=2)
    weights: Optional[BenchmarkWeights] = None
    max_concurrency: int = Field(default=4)
    max_samples: Optional[int] = None
    enable_baseline: bool = Field(default=True)
    enable_adversarial: bool = Field(default=True)
    attack_types: Optional[List[str]] = None


class StartBenchmarkResponse(BaseModel):
    """Response from starting a benchmark."""
    benchmark_id: UUID
    status: BenchmarkStatus
    message: str


class BenchmarkStatusResponse(BaseModel):
    """Status response for a benchmark."""
    benchmark_id: UUID
    status: BenchmarkStatus
    progress: Optional[float] = None
    completed_models: Optional[List[str]] = None
    current_model: Optional[str] = None
    error: Optional[str] = None


__all__ = [
    "BenchmarkMode",
    "BenchmarkStatus",
    "BenchmarkWeights",
    "BenchmarkConfig",
    "ModelMetrics",
    "MetricDeltas",
    "EvaluationResult",
    "ModelBenchmarkResult",
    "ModelRanking",
    "VulnerabilityHeatmapCell",
    "VulnerabilityHeatmap",
    "BenchmarkPerformance",
    "BenchmarkResult",
    "StartBenchmarkRequest",
    "StartBenchmarkResponse",
    "BenchmarkStatusResponse",
]
