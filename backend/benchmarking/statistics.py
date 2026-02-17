"""
Statistical Validation Module

Provides statistical functions for benchmark analysis:
- Standard deviation calculation
- Paired difference testing
- Confidence intervals
- Statistical significance testing
"""

import math
from typing import Dict, List, Optional, Tuple

import numpy as np


# =============================================================================
# Basic Statistics
# =============================================================================

def calculate_mean(values: List[float]) -> float:
    """Calculate arithmetic mean."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_standard_deviation(values: List[float]) -> float:
    """
    Calculate standard deviation (population).
    
    Formula: σ = sqrt(Σ(xi - μ)² / n)
    """
    if not values:
        return 0.0
    
    n = len(values)
    mean = calculate_mean(values)
    
    variance = sum((x - mean) ** 2 for x in values) / n
    return math.sqrt(variance)


def calculate_sample_std(values: List[float]) -> float:
    """
    Calculate sample standard deviation (unbiased estimator).
    
    Formula: s = sqrt(Σ(xi - x̄)² / (n-1))
    """
    if len(values) < 2:
        return 0.0
    
    n = len(values)
    mean = calculate_mean(values)
    
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    return math.sqrt(variance)


def calculate_variance(values: List[float]) -> float:
    """Calculate population variance."""
    if not values:
        return 0.0
    
    mean = calculate_mean(values)
    return sum((x - mean) ** 2 for x in values) / len(values)


# =============================================================================
# Standard Deviation for Metrics
# =============================================================================

class MetricStatistics:
    """Statistics calculator for evaluation metrics."""
    
    @staticmethod
    def calculate_all(
        hallucinations: List[float],
        toxicities: List[float],
        biases: List[float],
        confidences: List[float],
    ) -> Dict[str, float]:
        """
        Calculate standard deviations for all metrics.
        
        Returns:
            Dictionary with std for each metric
        """
        return {
            "std_hallucination": calculate_standard_deviation(hallucinations),
            "std_toxicity": calculate_standard_deviation(toxicities),
            "std_bias": calculate_standard_deviation(biases),
            "std_confidence": calculate_standard_deviation(confidences),
        }
    
    @staticmethod
    def calculate_sample_stds(
        hallucinations: List[float],
        toxicities: List[float],
        biases: List[float],
        confidences: List[float],
    ) -> Dict[str, float]:
        """
        Calculate sample standard deviations for all metrics.
        
        Returns:
            Dictionary with sample std for each metric
        """
        return {
            "sample_std_hallucination": calculate_sample_std(hallucinations),
            "sample_std_toxicity": calculate_sample_std(toxicities),
            "sample_std_bias": calculate_sample_std(biases),
            "sample_std_confidence": calculate_sample_std(confidences),
        }


# =============================================================================
# Confidence Intervals
# =============================================================================

def calculate_confidence_interval(
    values: List[float],
    confidence: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Calculate confidence interval for the mean.
    
    Args:
        values: List of values
        confidence: Confidence level (default 0.95 for 95%)
    
    Returns:
        Tuple of (lower_bound, upper_bound, margin_of_error)
    """
    if len(values) < 2:
        mean = calculate_mean(values)
        return mean, mean, 0.0
    
    n = len(values)
    mean = calculate_mean(values)
    std_error = calculate_sample_std(values) / math.sqrt(n)
    
    # Z-scores for common confidence levels
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }
    
    z = z_scores.get(confidence, 1.96)
    margin_of_error = z * std_error
    
    return mean - margin_of_error, mean + margin_of_error, margin_of_error


def calculate_mean_with_ci(
    values: List[float],
    confidence: float = 0.95,
) -> Dict[str, float]:
    """
    Calculate mean with confidence interval.
    
    Returns:
        Dictionary with mean, lower_ci, upper_ci, margin_of_error
    """
    if not values:
        return {
            "mean": 0.0,
            "lower_ci": 0.0,
            "upper_ci": 0.0,
            "margin_of_error": 0.0,
        }
    
    lower, upper, margin = calculate_confidence_interval(values, confidence)
    
    return {
        "mean": calculate_mean(values),
        "lower_ci": lower,
        "upper_ci": upper,
        "margin_of_error": margin,
    }


# =============================================================================
# Paired Difference Test
# =============================================================================

def calculate_paired_differences(
    baseline_values: List[float],
    adversarial_values: List[float],
) -> List[float]:
    """
    Calculate paired differences between baseline and adversarial.
    
    Di = R_base,i - R_adv,i
    
    Args:
        baseline_values: List of baseline values
        adversarial_values: List of adversarial values
    
    Returns:
        List of paired differences
    """
    if len(baseline_values) != len(adversarial_values):
        raise ValueError(
            "Baseline and adversarial must have same number of values"
        )
    
    return [b - a for b, a in zip(baseline_values, adversarial_values)]


def paired_t_test(
    baseline_values: List[float],
    adversarial_values: List[float],
    alpha: float = 0.05,
) -> Dict[str, any]:
    """
    Perform paired t-test for statistical significance.
    
    Tests whether the mean difference between paired observations
    is significantly different from zero.
    
    Args:
        baseline_values: List of baseline values
        adversarial_values: List of adversarial values
        alpha: Significance level (default 0.05)
    
    Returns:
        Dictionary with test results
    """
    if len(baseline_values) != len(adversarial_values):
        raise ValueError("Values must be paired (same length)")
    
    if len(baseline_values) < 2:
        return {
            "statistically_significant": False,
            "p_value": 1.0,
            "t_statistic": 0.0,
            "mean_difference": 0.0,
            "degrees_of_freedom": 0,
            "critical_value": None,
        }
    
    differences = calculate_paired_differences(baseline_values, adversarial_values)
    n = len(differences)
    mean_diff = calculate_mean(differences)
    std_diff = calculate_sample_std(differences)
    
    # Calculate t-statistic
    if std_diff == 0:
        t_stat = 0.0
    else:
        std_error = std_diff / math.sqrt(n)
        t_stat = mean_diff / std_error
    
    # Degrees of freedom
    df = n - 1
    
    # Approximate p-value using t-distribution
    # For large samples, t approaches z
    p_value = 2 * (1 - _normal_cdf(abs(t_stat)))
    
    # Critical value for two-tailed test
    critical_value = _normal_quantile(1 - alpha / 2)
    
    return {
        "statistically_significant": p_value < alpha,
        "p_value": p_value,
        "t_statistic": t_stat,
        "mean_difference": mean_diff,
        "degrees_of_freedom": df,
        "critical_value": critical_value,
        "sample_size": n,
    }


def _normal_cdf(x: float) -> float:
    """Approximate normal CDF using error function."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def _normal_quantile(p: float) -> float:
    """Approximate normal quantile (inverse CDF) using rational approximation."""
    # Rational approximation for p close to 0.5
    if p < 0.5:
        return -_normal_quantile(1 - p)
    
    if p > 0.999999:
        p = 0.999999
    
    # Rational approximation coefficients
    a1 = -3.969683028665376e1
    a2 = 2.209460984245205e2
    a3 = -2.759285104469687e2
    a4 = 1.383577518672690e2
    a5 = -3.066479806614716e1
    a6 = 2.506628277459239e0
    
    b1 = -5.447609879822406e1
    b2 = 1.615858368580409e2
    b3 = -1.556989798598866e2
    b4 = 6.680131188771972e1
    b5 = -1.328068155288572e1
    
    c1 = -7.784894002430293e-3
    c2 = -3.223964580411365e-1
    c3 = -2.400758277161838e0
    c4 = -2.549732539343734e0
    c5 = 4.374664141464968e0
    c6 = 2.938163982698783e0
    
    d1 = 7.784695709041462e-3
    d2 = 3.224671290700398e-1
    d3 = 2.445134137142996e0
    d4 = 3.754408661907416e0
    
    p_low = 0.02425
    p_high = 1 - p_low
    
    q = math.sqrt(-2 * math.log(1 - p))
    
    if p < p_low:
        r = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1
        )
    elif p <= p_high:
        r = (((((a1 * q + a2) * q + a3) * q + a4) * q + a5) * q + a6) / (
            ((((b1 * q + b2) * q + b3) * q + b4) * q + b5) * q + 1
        )
    else:
        r = (((((c1 * q + c2) * q + c3) * q + c4) * q + c5) * q + c6) / (
            (((d1 * q + d2) * q + d3) * q + d4) * q + 1
        )
    
    return r


# =============================================================================
# Effect Size
# =============================================================================

def cohens_d(
    group1: List[float],
    group2: List[float],
) -> float:
    """
    Calculate Cohen's d effect size.
    
    Measures the standardized difference between two groups.
    
    Interpretation:
    - |d| < 0.2: negligible
    - 0.2 <= |d| < 0.5: small
    - 0.5 <= |d| < 0.8: medium
    - |d| >= 0.8: large
    
    Args:
        group1: First group of values
        group2: Second group of values
    
    Returns:
        Cohen's d value
    """
    n1 = len(group1)
    n2 = len(group2)
    
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1 = calculate_mean(group1)
    mean2 = calculate_mean(group2)
    std1 = calculate_sample_std(group1)
    std2 = calculate_sample_std(group2)
    
    # Pooled standard deviation
    pooled_std = math.sqrt(
        ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
    )
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std


# =============================================================================
# Vulnerability Consistency
# =============================================================================

def calculate_vulnerability_consistency(
    baseline_robustness: List[float],
    adversarial_robustness: List[float],
) -> Dict[str, float]:
    """
    Calculate vulnerability consistency metrics.
    
    How consistently does the model degrade under adversarial attacks?
    
    Args:
        baseline_robustness: List of baseline robustness values
        adversarial_robustness: List of adversarial robustness values
    
    Returns:
        Dictionary with consistency metrics
    """
    if len(baseline_robustness) != len(adversarial_robustness):
        raise ValueError("Lists must have same length")
    
    if not baseline_robustness:
        return {
            "mean_delta": 0.0,
            "std_delta": 0.0,
            "consistency_score": 0.0,
        }
    
    differences = [
        b - a for b, a in zip(baseline_robustness, adversarial_robustness)
    ]
    
    mean_delta = calculate_mean(differences)
    std_delta = calculate_standard_deviation(differences)
    
    # Consistency: higher std = less consistent degradation
    # Normalize to 0-1 scale where 1 is perfectly consistent
    consistency_score = 1.0 - min(std_delta * 2, 1.0)
    
    return {
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "consistency_score": consistency_score,
    }


# =============================================================================
# Summary Statistics
# =============================================================================

def generate_summary_statistics(
    values: List[float],
    confidence: float = 0.95,
) -> Dict[str, float]:
    """
    Generate comprehensive summary statistics.
    
    Args:
        values: List of values
        confidence: Confidence level for CI
    
    Returns:
        Dictionary with all summary statistics
    """
    if not values:
        return {
            "count": 0,
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "median": 0.0,
            "q25": 0.0,
            "q75": 0.0,
        }
    
    sorted_values = sorted(values)
    n = len(values)
    
    return {
        "count": n,
        "mean": calculate_mean(values),
        "std": calculate_standard_deviation(values),
        "sample_std": calculate_sample_std(values),
        "min": min(values),
        "max": max(values),
        "median": sorted_values[n // 2] if n % 2 == 1 else 
                  (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2,
        "q25": sorted_values[n // 4],
        "q75": sorted_values[3 * n // 4],
    }


__all__ = [
    "calculate_mean",
    "calculate_standard_deviation",
    "calculate_sample_std",
    "calculate_variance",
    "MetricStatistics",
    "calculate_confidence_interval",
    "calculate_mean_with_ci",
    "calculate_paired_differences",
    "paired_t_test",
    "cohens_d",
    "calculate_vulnerability_consistency",
    "generate_summary_statistics",
]
