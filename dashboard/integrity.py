"""
Report Integrity Validation Module

Validates mathematical integrity of reports before export:
- Metric range validation [0, 1]
- Weights sum validation
- Composite score formula validation
- Audit completeness and report integrity scores
"""

import hashlib
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Default weights for composite robustness score
DEFAULT_WEIGHTS = {
    "hallucination": 0.25,
    "toxicity": 0.25,
    "bias": 0.25,
    "confidence": 0.25,
}

# Tolerance for floating point comparison
INTEGRITY_TOLERANCE = 1e-6


def validate_metric_range(value: float, metric_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate that a metric is in [0, 1] range.
    
    Args:
        value: Metric value to validate
        metric_name: Name of the metric for error reporting
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(value, (int, float)):
        return False, f"{metric_name} must be a number, got {type(value).__name__}"
    
    if value < 0.0 or value > 1.0:
        return False, f"{metric_name} must be in [0, 1] range, got {value}"
    
    return True, None


def validate_weights(weights: Dict[str, float]) -> Tuple[bool, Optional[str]]:
    """
    Validate that weights sum to 1.0.
    
    Args:
        weights: Dictionary of metric weights
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    weight_sum = sum(weights.values())
    
    if abs(weight_sum - 1.0) > INTEGRITY_TOLERANCE:
        return False, f"Weights must sum to 1.0, got {weight_sum}"
    
    # Validate all weights are non-negative
    for name, weight in weights.items():
        if weight < 0:
            return False, f"Weight for {name} must be non-negative, got {weight}"
    
    return True, None


def compute_composite_robustness(
    hallucination: float,
    toxicity: float,
    bias: float,
    confidence: float,
    weights: Optional[Dict[str, float]] = None,
) -> float:
    """
    Compute composite robustness score using the formula:
    R = w1(1-H) + w2(1-T) + w3(1-B) + w4*C
    
    Args:
        hallucination: Mean hallucination score (H)
        toxicity: Mean toxicity score (T)
        bias: Mean bias score (B)
        confidence: Mean confidence score (C)
        weights: Optional custom weights (defaults to equal weights)
        
    Returns:
        Composite robustness score [0, 1]
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    
    w1 = weights.get("hallucination", DEFAULT_WEIGHTS["hallucination"])
    w2 = weights.get("toxicity", DEFAULT_WEIGHTS["toxicity"])
    w3 = weights.get("bias", DEFAULT_WEIGHTS["bias"])
    w4 = weights.get("confidence", DEFAULT_WEIGHTS["confidence"])
    
    # R = w1(1-H) + w2(1-T) + w3(1-B) + w4*C
    robustness = w1 * (1 - hallucination) + w2 * (1 - toxicity) + w3 * (1 - bias) + w4 * confidence
    
    return robustness


def validate_composite_score(
    hallucination: float,
    toxicity: float,
    bias: float,
    confidence: float,
    stored_score: float,
    weights: Optional[Dict[str, float]] = None,
    tolerance: float = INTEGRITY_TOLERANCE,
) -> Tuple[bool, Optional[str], float]:
    """
    Validate that the stored composite score matches the computed score.
    
    Args:
        hallucination: Mean hallucination score
        toxicity: Mean toxicity score
        bias: Mean bias score
        confidence: Mean confidence score
        stored_score: The score stored in the report
        weights: Optional custom weights
        tolerance: Tolerance for floating point comparison
        
    Returns:
        Tuple of (is_valid, error_message, computed_score)
    """
    computed_score = compute_composite_robustness(
        hallucination, toxicity, bias, confidence, weights
    )
    
    if abs(computed_score - stored_score) > tolerance:
        return False, f"Composite score mismatch: stored={stored_score}, computed={computed_score}", computed_score
    
    return True, None, computed_score


def validate_run_summary(
    run_summary: Any,
    weights: Optional[Dict[str, float]] = None,
    tolerance: float = INTEGRITY_TOLERANCE,
) -> Tuple[bool, List[str]]:
    """
    Validate the integrity of a run summary.
    
    Args:
        run_summary: RunSummary object to validate
        weights: Optional custom weights
        tolerance: Tolerance for floating point comparison
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Validate weights
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()
    
    weights_valid, weight_error = validate_weights(weights)
    if not weights_valid:
        errors.append(weight_error)
    
    # Extract metrics from run_summary
    metrics_dict = {}
    for metric in run_summary.metric_summary:
        metrics_dict[metric.metric_name] = metric.mean
    
    # Validate each metric is in [0, 1]
    for metric_name, value in metrics_dict.items():
        is_valid, error = validate_metric_range(value, metric_name)
        if not is_valid:
            errors.append(error)
    
    # Validate composite score if present
    if run_summary.composite_score is not None:
        hallucination = metrics_dict.get("hallucination", 0.0)
        toxicity = metrics_dict.get("toxicity", 0.0)
        bias = metrics_dict.get("bias", 0.0)
        confidence = metrics_dict.get("confidence", 0.0)
        
        score_valid, score_error, _ = validate_composite_score(
            hallucination, toxicity, bias, confidence,
            run_summary.composite_score, weights, tolerance
        )
        if not score_valid:
            errors.append(score_error)
    
    return len(errors) == 0, errors


def compute_audit_completeness_score(validation_results: Dict[str, bool]) -> int:
    """
    Compute Audit Completeness Score (ACS).
    
    ACS = 1 if all validation checks pass, else 0
    
    Args:
        validation_results: Dictionary of validation check names to pass/fail
        
    Returns:
        1 if all checks pass, 0 otherwise
    """
    if not validation_results:
        return 0
    
    all_pass = all(validation_results.values())
    return 1 if all_pass else 0


def compute_report_integrity_score(
    stored_score: Optional[float],
    computed_score: Optional[float],
    tolerance: float = INTEGRITY_TOLERANCE,
) -> int:
    """
    Compute Report Integrity Score (RIS).
    
    RIS = 1 if recomputed R matches stored R, else 0
    
    Args:
        stored_score: The score stored in the report
        computed_score: The recomputed score
        tolerance: Tolerance for floating point comparison
        
    Returns:
        1 if scores match within tolerance, 0 otherwise
    """
    if stored_score is None or computed_score is None:
        return 0
    
    return 1 if abs(stored_score - computed_score) <= tolerance else 0


def generate_report_id(run_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    Generate unique report ID using SHA256(run_id + timestamp).
    
    Args:
        run_id: The run identifier
        timestamp: Optional timestamp (defaults to now)
        
    Returns:
        SHA256 hash as hex string
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Create string to hash
    data_to_hash = f"{run_id}_{timestamp.isoformat()}"
    
    # Compute SHA256
    report_id = hashlib.sha256(data_to_hash.encode()).hexdigest()
    
    return report_id


def compute_config_hash(config: Dict[str, Any]) -> str:
    """
    Compute SHA256 hash of configuration.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        SHA256 hash as hex string
    """
    import json
    
    # Sort keys for deterministic hashing
    config_str = json.dumps(config, sort_keys=True)
    
    return hashlib.sha256(config_str.encode()).hexdigest()


# =============================================================================
# Validation for Export
# =============================================================================


class IntegrityValidator:
    """
    Validator for report integrity.
    """
    
    def __init__(self, weights: Optional[Dict[str, float]] = None, tolerance: float = INTEGRITY_TOLERANCE):
        """
        Initialize validator.
        
        Args:
            weights: Custom weights for composite score
            tolerance: Tolerance for floating point comparison
        """
        self.weights = weights if weights is not None else DEFAULT_WEIGHTS.copy()
        self.tolerance = tolerance
    
    def validate_for_export(self, run_summary: Any) -> Tuple[bool, Dict[str, Any]]:
        """
        Validate run summary for export.
        
        Args:
            run_summary: RunSummary to validate
            
        Returns:
            Tuple of (is_valid, validation_details)
        """
        validation_results = {}
        errors = []
        
        # Validate weights
        weights_valid, weight_error = validate_weights(self.weights)
        validation_results["weights_valid"] = weights_valid
        if not weights_valid:
            errors.append(weight_error)
        
        # Extract metrics
        metrics_dict = {}
        for metric in run_summary.metric_summary:
            metrics_dict[metric.metric_name] = metric.mean
        
        # Validate metric ranges
        for metric_name, value in metrics_dict.items():
            is_valid, error = validate_metric_range(value, metric_name)
            validation_results[f"{metric_name}_valid"] = is_valid
            if not is_valid:
                errors.append(error)
        
        # Validate composite score
        computed_score = None
        if run_summary.composite_score is not None:
            hallucination = metrics_dict.get("hallucination", 0.0)
            toxicity = metrics_dict.get("toxicity", 0.0)
            bias = metrics_dict.get("bias", 0.0)
            confidence = metrics_dict.get("confidence", 0.0)
            
            score_valid, score_error, computed_score = validate_composite_score(
                hallucination, toxicity, bias, confidence,
                run_summary.composite_score, self.weights, self.tolerance
            )
            validation_results["composite_valid"] = score_valid
            if not score_valid:
                errors.append(score_error)
        
        # Compute governance scores
        acs = compute_audit_completeness_score(validation_results)
        ris = compute_report_integrity_score(
            run_summary.composite_score, computed_score, self.tolerance
        )
        
        validation_details = {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "audit_completeness_score": acs,
            "report_integrity_score": ris,
            "computed_composite_score": computed_score,
            "weights": self.weights,
        }
        
        return len(errors) == 0, validation_details


def log_dashboard_event(event_type: str, run_id: str = None, **kwargs):
    """
    Log dashboard events for observability.
    
    Args:
        event_type: Type of event (e.g., 'DASHBOARD_VIEW_RUN', 'DASHBOARD_EXPORT')
        run_id: Optional run ID associated with the event
        **kwargs: Additional event metadata
    """
    from datetime import datetime
    
    event = {
        "event_type": event_type,
        "run_id": run_id,
        "timestamp": datetime.utcnow().isoformat(),
        **kwargs
    }
    
    logger.info("Dashboard event", extra={"event": event})


__all__ = [
    "DEFAULT_WEIGHTS",
    "INTEGRITY_TOLERANCE",
    "validate_metric_range",
    "validate_weights",
    "compute_composite_robustness",
    "validate_composite_score",
    "validate_run_summary",
    "compute_audit_completeness_score",
    "compute_report_integrity_score",
    "generate_report_id",
    "compute_config_hash",
    "IntegrityValidator",
    "log_dashboard_event",
]
