"""
Logging Schema Definitions

Defines Pydantic models for structured log entries.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Log level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Component(str, Enum):
    """System components for logging."""

    ORCHESTRATOR = "orchestrator"
    MODEL_EXECUTOR = "model_executor"
    ATTACKER = "attacker"
    DEFENDER = "defender"
    JUDGE = "judge"
    SCORING = "scoring"
    API = "api"
    DATABASE = "database"
    AGENT = "agent"


class BaseLogSchema(BaseModel):
    """Base schema for all log entries."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="ISO 8601 timestamp of the log entry"
    )
    level: LogLevel = Field(
        description="Log level"
    )
    run_id: Optional[UUID] = Field(
        default=None,
        description="Evaluation run ID for correlation"
    )
    component: Component = Field(
        description="Component that generated the log"
    )
    message: str = Field(
        description="Log message"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional structured metadata"
    )


class EvaluationLogSchema(BaseLogSchema):
    """Schema for evaluation-related logs."""

    sample_id: Optional[str] = Field(
        default=None,
        description="Sample ID being processed"
    )
    attack_type: Optional[str] = Field(
        default=None,
        description="Type of attack applied"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Model being evaluated"
    )


class MetricsLogSchema(BaseLogSchema):
    """Schema for metrics and observability logs."""

    latency_ms: Optional[float] = Field(
        default=None,
        description="Processing latency in milliseconds"
    )
    tokens_generated: Optional[int] = Field(
        default=None,
        description="Number of tokens generated"
    )
    attack_chain_depth: Optional[int] = Field(
        default=None,
        description="Depth of attack chain"
    )
    throughput_samples_per_sec: Optional[float] = Field(
        default=None,
        description="Processing throughput"
    )
    memory_usage_mb: Optional[float] = Field(
        default=None,
        description="Memory usage in MB"
    )


class ErrorLogSchema(BaseLogSchema):
    """Schema for error logs."""

    error_type: str = Field(
        description="Type of error"
    )
    error_message: str = Field(
        description="Error message"
    )
    stack_trace: Optional[str] = Field(
        default=None,
        description="Stack trace if available"
    )
    recoverable: bool = Field(
        default=True,
        description="Whether the error is recoverable"
    )


class LifecycleLogSchema(BaseLogSchema):
    """Schema for lifecycle event logs."""

    event: str = Field(
        description="Lifecycle event name"
    )
    previous_state: Optional[str] = Field(
        default=None,
        description="Previous state"
    )
    new_state: str = Field(
        description="New state"
    )


# =============================================================================
# Log entry schemas for specific components
# =============================================================================

class OrchestratorLogSchema(EvaluationLogSchema):
    """Schema for orchestrator logs."""

    total_samples: Optional[int] = Field(
        default=None,
        description="Total samples to process"
    )
    processed_samples: Optional[int] = Field(
        default=None,
        description="Samples processed so far"
    )
    failed_samples: Optional[int] = Field(
        default=None,
        description="Number of failed samples"
    )


class ModelExecutorLogSchema(EvaluationLogSchema):
    """Schema for model executor logs."""

    model_name: str = Field(
        description="Model name"
    )
    model_version: str = Field(
        description="Model version"
    )
    generation_time_ms: float = Field(
        description="Time taken for generation"
    )
    input_tokens: int = Field(
        description="Number of input tokens"
    )
    output_tokens: int = Field(
        description="Number of output tokens"
    )
    device: str = Field(
        description="Device used for inference"
    )


class ScoringLogSchema(BaseLogSchema):
    """Schema for scoring logs."""

    hallucination_score: Optional[float] = Field(
        default=None,
        description="Hallucination score [0, 1]"
    )
    toxicity_score: Optional[float] = Field(
        default=None,
        description="Toxicity score [0, 1]"
    )
    bias_score: Optional[float] = Field(
        default=None,
        description="Bias score [0, 1]"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Confidence score [0, 1]"
    )
    composite_score: Optional[float] = Field(
        default=None,
        description="Composite robustness score"
    )


class APILogSchema(BaseLogSchema):
    """Schema for API request/response logs."""

    method: str = Field(
        description="HTTP method"
    )
    path: str = Field(
        description="Request path"
    )
    status_code: Optional[int] = Field(
        default=None,
        description="Response status code"
    )
    request_id: Optional[str] = Field(
        default=None,
        description="Request ID for tracing"
    )
    user_agent: Optional[str] = Field(
        default=None,
        description="User agent string"
    )
    response_time_ms: Optional[float] = Field(
        default=None,
        description="Response time in milliseconds"
    )


# =============================================================================
# Log aggregation schemas
# =============================================================================

class AggregatedMetricsSchema(BaseModel):
    """Schema for aggregated evaluation metrics."""

    run_id: UUID = Field(
        description="Evaluation run ID"
    )
    total_samples: int = Field(
        description="Total number of samples"
    )
    successful_samples: int = Field(
        description="Number of successfully processed samples"
    )
    failed_samples: int = Field(
        description="Number of failed samples"
    )
    
    # Aggregate scores
    mean_hallucination: Optional[float] = Field(
        default=None,
        description="Mean hallucination score"
    )
    mean_toxicity: Optional[float] = Field(
        default=None,
        description="Mean toxicity score"
    )
    mean_bias: Optional[float] = Field(
        default=None,
        description="Mean bias score"
    )
    mean_confidence: Optional[float] = Field(
        default=None,
        description="Mean confidence score"
    )
    mean_robustness: Optional[float] = Field(
        default=None,
        description="Mean robustness score"
    )
    composite_score: Optional[float] = Field(
        default=None,
        description="Final composite score"
    )
    
    # Timing metrics
    total_processing_time_ms: float = Field(
        description="Total processing time in milliseconds"
    )
    mean_sample_time_ms: float = Field(
        description="Mean time per sample in milliseconds"
    )
    throughput_samples_per_sec: float = Field(
        description="Processing throughput"
    )
    
    # Error summary
    error_types: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of each error type"
    )


class RunSummarySchema(BaseModel):
    """Schema for evaluation run summary."""

    run_id: UUID = Field(
        description="Evaluation run ID"
    )
    model_name: str = Field(
        description="Model name"
    )
    dataset_version: str = Field(
        description="Dataset version"
    )
    status: str = Field(
        description="Run status"
    )
    metrics: AggregatedMetricsSchema = Field(
        description="Aggregated metrics"
    )
    artifacts_path: str = Field(
        description="Path to run artifacts"
    )
    completed_at: datetime = Field(
        description="Completion timestamp"
    )
