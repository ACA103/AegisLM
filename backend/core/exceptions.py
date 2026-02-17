"""
Custom Exception Classes for AegisLM Backend

Defines domain-specific exceptions for the evaluation framework.
"""

from typing import Any, Dict, Optional


class AegisLMException(Exception):
    """Base exception for all AegisLM errors."""

    def __init__(
        self,
        message: str,
        code: str = "AEGISLM_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error": self.__class__.__name__,
            "code": self.code,
            "message": self.message,
            "details": self.details
        }


# ============================================================================
# Configuration Exceptions
# ============================================================================

class ConfigurationError(AegisLMException):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="CONFIG_ERROR", details=details)


class WeightValidationError(ConfigurationError):
    """Raised when scoring weights don't sum to 1.0."""

    def __init__(self, total: float):
        super().__init__(
            f"Scoring weights must sum to 1.0, got {total}",
            details={"total_weight": total}
        )


# ============================================================================
# Database Exceptions
# ============================================================================

class DatabaseError(AegisLMException):
    """Raised when database operations fail."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class RecordNotFoundError(DatabaseError):
    """Raised when a database record is not found."""

    def __init__(self, model: str, identifier: Any):
        super().__init__(
            f"{model} not found",
            details={"model": model, "identifier": str(identifier)}
        )


class MigrationError(DatabaseError):
    """Raised when database migration fails."""

    def __init__(self, message: str):
        super().__init__(message, code="MIGRATION_ERROR")


# ============================================================================
# Model/Execution Exceptions
# ============================================================================

class ModelError(AegisLMException):
    """Raised when model loading or execution fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="MODEL_ERROR", details=details)


class ModelNotFoundError(ModelError):
    """Raised when a model is not found in registry."""

    def __init__(self, model_name: str, version: Optional[str] = None):
        details = {"model_name": model_name}
        if version:
            details["version"] = version
        super().__init__(
            f"Model '{model_name}' not found",
            details=details
        )


class ModelLoadingError(ModelError):
    """Raised when model fails to load."""

    def __init__(self, model_name: str, reason: str):
        super().__init__(
            f"Failed to load model '{model_name}': {reason}",
            details={"model_name": model_name, "reason": reason}
        )


class GenerationError(ModelError):
    """Raised when text generation fails."""

    def __init__(self, message: str):
        super().__init__(message, code="GENERATION_ERROR")


class DeviceError(ModelError):
    """Raised when device (CUDA/CPU) configuration fails."""

    def __init__(self, message: str):
        super().__init__(message, code="DEVICE_ERROR")


# ============================================================================
# Evaluation Exceptions
# ============================================================================

class EvaluationError(AegisLMException):
    """Raised when evaluation pipeline fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="EVALUATION_ERROR", details=details)


class EvaluationTimeoutError(EvaluationError):
    """Raised when evaluation exceeds timeout."""

    def __init__(self, run_id: str, timeout_seconds: int):
        super().__init__(
            f"Evaluation run '{run_id}' timed out after {timeout_seconds}s",
            details={"run_id": run_id, "timeout_seconds": timeout_seconds}
        )


class EvaluationCancelledError(EvaluationError):
    """Raised when evaluation is cancelled."""

    def __init__(self, run_id: str):
        super().__init__(
            f"Evaluation run '{run_id}' was cancelled",
            details={"run_id": run_id}
        )


# ============================================================================
# Scoring Exceptions
# ============================================================================

class ScoringError(AegisLMException):
    """Raised when scoring computation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="SCORING_ERROR", details=details)


class InvalidMetricError(ScoringError):
    """Raised when a metric value is outside valid range [0, 1]."""

    def __init__(self, metric_name: str, value: float):
        super().__init__(
            f"Metric '{metric_name}' must be in [0, 1], got {value}",
            details={"metric": metric_name, "value": value}
        )


# ============================================================================
# API Exceptions
# ============================================================================

class APIError(AegisLMException):
    """Raised for general API errors."""

    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, code="API_ERROR")
        self.status_code = status_code


class ValidationError(APIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        super().__init__(message, status_code=422)
        self.code = "VALIDATION_ERROR"
        self.details = details


class NotFoundError(APIError):
    """Raised when resource is not found."""

    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            f"{resource} not found: {identifier}",
            status_code=404
        )
        self.code = "NOT_FOUND"


# ============================================================================
# Agent Exceptions
# ============================================================================

class AgentError(AegisLMException):
    """Raised when agent execution fails."""

    def __init__(self, message: str, agent_type: Optional[str] = None):
        details = {}
        if agent_type:
            details["agent_type"] = agent_type
        super().__init__(message, code="AGENT_ERROR", details=details)


class AgentTimeoutError(AgentError):
    """Raised when agent execution times out."""

    def __init__(self, agent_type: str, timeout_seconds: int):
        super().__init__(
            f"Agent '{agent_type}' timed out after {timeout_seconds}s",
            agent_type=agent_type
        )


class AgentInitializationError(AgentError):
    """Raised when agent fails to initialize."""

    def __init__(self, agent_type: str, reason: str):
        super().__init__(
            f"Failed to initialize agent '{agent_type}': {reason}",
            agent_type=agent_type
        )
