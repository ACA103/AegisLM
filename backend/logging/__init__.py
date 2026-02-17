"""
Logging Module

Structured logging framework for AegisLM.
"""

from backend.logging.logger import (
    StructuredLogger,
    get_logger,
    default_logger,
)
from backend.logging.schema import (
    LogLevel,
    Component,
    BaseLogSchema,
    EvaluationLogSchema,
    MetricsLogSchema,
    ErrorLogSchema,
    LifecycleLogSchema,
    OrchestratorLogSchema,
    ModelExecutorLogSchema,
    ScoringLogSchema,
    APILogSchema,
    AggregatedMetricsSchema,
    RunSummarySchema,
)

__all__ = [
    # Logger
    "StructuredLogger",
    "get_logger",
    "default_logger",
    # Schema
    "LogLevel",
    "Component",
    "BaseLogSchema",
    "EvaluationLogSchema",
    "MetricsLogSchema",
    "ErrorLogSchema",
    "LifecycleLogSchema",
    "OrchestratorLogSchema",
    "ModelExecutorLogSchema",
    "ScoringLogSchema",
    "APILogSchema",
    "AggregatedMetricsSchema",
    "RunSummarySchema",
]
