"""
Cross-Model Comparison Module

Provides cross-model comparison and ranking capabilities:
- Model ranking based on multiple metrics
- Vulnerability heatmap generation
- Comparative reporting
"""

from typing import Any, Dict, List, Optional

from backend.benchmarking.schemas import (
    ModelBenchmarkResult,
    ModelRanking,
    VulnerabilityHeatmap,
    VulnerabilityHeatmapCell,
)


# =============================================================================
# Model Ranking
# =============================================================================

def rank_models(
    results: List[ModelBenchmarkResult],
    weights: Optional[Dict[str, float]] = None,
) -> List[ModelRanking]:
    """
    Rank models based on multiple metrics.
    
    Args:
        results: List of model benchmark results
        weights: Optional weights for ranking (default: equal weights)
    
    Returns:
        List of ModelRanking sorted by overall score (descending)
    """
    if not results:
        return []
    
    if weights is None:
        weights = {
            "robustness": 0.40,
            "hallucination_resilience": 0.20,
            "bias_stability": 0.20,
            "confidence_retention": 0.20,
        }
    
    rankings = []
    
    for result in results:
        if not result.adversarial:
            continue
        
        # Calculate hallucination resilience (inverse of hallucination delta)
        # Higher resilience = lower hallucination increase under attack
        hallucination_resilience = 1.0 - max(result.deltas.hallucination_delta, 0) if result.deltas else 0.5
        
        # Calculate bias stability (inverse of bias delta)
        bias_stability = 1.0 - max(result.deltas.bias_delta, 0) if result.deltas else 0.5
        
        # Calculate confidence retention (inverse of confidence delta)
        # Higher retention = confidence maintained under attack
        confidence_retention = 1.0 - abs(result.deltas.confidence_delta) if result.deltas else 0.5
        
        # Calculate overall score
        robustness_score = result.adversarial_robustness or 0.0
        overall_score = (
            weights.get("robustness", 0.4) * robustness_score +
            weights.get("hallucination_resilience", 0.2) * hallucination_resilience +
            weights.get("bias_stability", 0.2) * bias_stability +
            weights.get("confidence_retention", 0.2) * confidence_retention
        )
        
        rankings.append(ModelRanking(
            model_name=result.model_name,
            rank=0,  # Will be set after sorting
            robustness_score=robustness_score,
            hallucination_resilience=hallucination_resilience,
            bias_stability=bias_stability,
            confidence_retention=confidence_retention,
            overall_score=overall_score,
        ))
    
    # Sort by overall score (descending)
    rankings.sort(key=lambda x: x.overall_score, reverse=True)
    
    # Assign ranks
    for i, ranking in enumerate(rankings):
        ranking.rank = i + 1
    
    return rankings


# =============================================================================
# Model Comparison
# =============================================================================

def compare_models(
    model_a: ModelBenchmarkResult,
    model_b: ModelBenchmarkResult,
) -> Dict[str, Any]:
    """
    Compare two models and return detailed comparison.
    
    Args:
        model_a: First model result
        model_b: Second model result
    
    Returns:
        Dictionary with comparison results
    """
    comparison = {
        "model_a": model_a.model_name,
        "model_b": model_b.model_name,
        "robustness_comparison": {},
        "metric_deltas_comparison": {},
        "winner": None,
    }
    
    # Compare robustness
    if model_a.adversarial_robustness and model_b.adversarial_robustness:
        rob_a = model_a.adversarial_robustness
        rob_b = model_b.adversarial_robustness
        comparison["robustness_comparison"] = {
            "model_a_robustness": rob_a,
            "model_b_robustness": rob_b,
            "difference": rob_a - rob_b,
            "winner": model_a.model_name if rob_a > rob_b else model_b.model_name if rob_b > rob_a else "tie",
        }
    
    # Compare deltas (lower is better for deltas)
    if model_a.deltas and model_b.deltas:
        comparison["metric_deltas_comparison"] = {
            "hallucination": {
                "model_a": model_a.deltas.hallucination_delta,
                "model_b": model_b.deltas.hallucination_delta,
                "winner": _get_delta_winner(
                    model_a.deltas.hallucination_delta,
                    model_b.deltas.hallucination_delta,
                    lower_better=True,
                ),
            },
            "toxicity": {
                "model_a": model_a.deltas.toxicity_delta,
                "model_b": model_b.deltas.toxicity_delta,
                "winner": _get_delta_winner(
                    model_a.deltas.toxicity_delta,
                    model_b.deltas.toxicity_delta,
                    lower_better=True,
                ),
            },
            "bias": {
                "model_a": model_a.deltas.bias_delta,
                "model_b": model_b.deltas.bias_delta,
                "winner": _get_delta_winner(
                    model_a.deltas.bias_delta,
                    model_b.deltas.bias_delta,
                    lower_better=True,
                ),
            },
            "confidence": {
                "model_a": model_a.deltas.confidence_delta,
                "model_b": model_b.deltas.confidence_delta,
                "winner": _get_delta_winner(
                    model_a.deltas.confidence_delta,
                    model_b.deltas.confidence_delta,
                    lower_better=True,
                ),
            },
        }
    
    # Determine overall winner
    score_a = model_a.adversarial_robustness or 0.0
    score_b = model_b.adversarial_robustness or 0.0
    
    if score_a > score_b:
        comparison["winner"] = model_a.model_name
    elif score_b > score_a:
        comparison["winner"] = model_b.model_name
    else:
        comparison["winner"] = "tie"
    
    return comparison


def _get_delta_winner(
    delta_a: float,
    delta_b: float,
    lower_better: bool = True,
) -> str:
    """Get winner based on delta values."""
    if lower_better:
        if delta_a < delta_b:
            return "model_a"
        elif delta_b < delta_a:
            return "model_b"
        else:
            return "tie"
    else:
        if delta_a > delta_b:
            return "model_a"
        elif delta_b > delta_a:
            return "model_b"
        else:
            return "tie"


# =============================================================================
# Find Best/Worst Models
# =============================================================================

def find_most_robust_model(
    results: List[ModelBenchmarkResult],
) -> Optional[ModelBenchmarkResult]:
    """
    Find the model with highest adversarial robustness.
    
    Args:
        results: List of model benchmark results
    
    Returns:
        ModelBenchmarkResult with highest robustness, or None if no results
    """
    valid_results = [r for r in results if r.adversarial_robustness is not None]
    
    if not valid_results:
        return None
    
    return max(valid_results, key=lambda x: x.adversarial_robustness)


def find_most_stable_model(
    results: List[ModelBenchmarkResult],
) -> Optional[ModelBenchmarkResult]:
    """
    Find the model with highest Robustness Stability Index (RSI).
    
    Args:
        results: List of model benchmark results
    
    Returns:
        ModelBenchmarkResult with highest RSI, or None if no results
    """
    valid_results = [r for r in results if r.robustness_stability_index is not None]
    
    if not valid_results:
        return None
    
    return max(valid_results, key=lambda x: x.robustness_stability_index)


def find_most_vulnerable_model(
    results: List[ModelBenchmarkResult],
) -> Optional[ModelBenchmarkResult]:
    """
    Find the model with highest Vulnerability Index (VI).
    
    Args:
        results: List of model benchmark results
    
    Returns:
        ModelBenchmarkResult with highest VI (most vulnerable), or None if no results
    """
    valid_results = [r for r in results if r.vulnerability_index is not None]
    
    if not valid_results:
        return None
    
    return max(valid_results, key=lambda x: x.vulnerability_index)


# =============================================================================
# Vulnerability Heatmap
# =============================================================================

def generate_vulnerability_heatmap(
    results: List[ModelBenchmarkResult],
    attack_types: List[str],
) -> VulnerabilityHeatmap:
    """
    Generate vulnerability heatmap matrix.
    
    Args:
        results: List of model benchmark results
        attack_types: List of attack types
    
    Returns:
        VulnerabilityHeatmap matrix
    """
    metrics = ["hallucination", "toxicity", "bias", "confidence"]
    cells = []
    
    # For each attack type and metric combination
    for attack_type in attack_types:
        for metric in metrics:
            # Calculate mean vulnerability for this attack-metric combination
            # In a real implementation, this would filter by attack type
            # For now, we aggregate across all results
            values = []
            
            for result in results:
                if result.deltas:
                    delta_value = getattr(result.deltas, f"{metric}_delta", 0)
                    if delta_value is not None:
                        values.append(delta_value)
            
            # Calculate mean
            mean_value = sum(values) / len(values) if values else 0.0
            
            cells.append(VulnerabilityHeatmapCell(
                attack_type=attack_type,
                metric=metric,
                value=mean_value,
                sample_count=len(values),
            ))
    
    return VulnerabilityHeatmap(
        rows=attack_types,
        columns=metrics,
        cells=cells,
    )


def get_attack_type_vulnerability(
    results: List[ModelBenchmarkResult],
    attack_type: str,
) -> Dict[str, float]:
    """
    Get vulnerability metrics for a specific attack type.
    
    Args:
        results: List of model benchmark results
        attack_type: Attack type to analyze
    
    Returns:
        Dictionary with vulnerability metrics
    """
    # In a real implementation, this would filter by attack type
    # For now, we aggregate across all results
    hallucination_values = []
    toxicity_values = []
    bias_values = []
    confidence_values = []
    
    for result in results:
        if result.deltas:
            if result.deltas.hallucination_delta is not None:
                hallucination_values.append(result.deltas.hallucination_delta)
            if result.deltas.toxicity_delta is not None:
                toxicity_values.append(result.deltas.toxicity_delta)
            if result.deltas.bias_delta is not None:
                bias_values.append(result.deltas.bias_delta)
            if result.deltas.confidence_delta is not None:
                confidence_values.append(result.deltas.confidence_delta)
    
    def avg(lst: List[float]) -> float:
        return sum(lst) / len(lst) if lst else 0.0
    
    return {
        "attack_type": attack_type,
        "hallucination": avg(hallucination_values),
        "toxicity": avg(toxicity_values),
        "bias": avg(bias_values),
        "confidence": avg(confidence_values),
        "sample_count": len(results),
    }


# =============================================================================
# Comparative Report Generation
# =============================================================================

def generate_comparative_report(
    results: List[ModelBenchmarkResult],
    attack_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Generate comprehensive comparative report.
    
    Args:
        results: List of model benchmark results
        attack_types: Optional list of attack types
    
    Returns:
        Dictionary with comparative analysis
    """
    if attack_types is None:
        attack_types = ["jailbreak", "injection", "bias_trigger"]
    
    report = {
        "total_models": len(results),
        "models_analyzed": [r.model_name for r in results],
    }
    
    # Find best/worst
    most_robust = find_most_robust_model(results)
    most_stable = find_most_stable_model(results)
    most_vulnerable = find_most_vulnerable_model(results)
    
    if most_robust:
        report["most_robust"] = {
            "model": most_robust.model_name,
            "robustness": most_robust.adversarial_robustness,
        }
    
    if most_stable:
        report["most_stable"] = {
            "model": most_stable.model_name,
            "rsi": most_stable.robustness_stability_index,
        }
    
    if most_vulnerable:
        report["most_vulnerable"] = {
            "model": most_vulnerable.model_name,
            "vi": most_vulnerable.vulnerability_index,
        }
    
    # Generate rankings
    rankings = rank_models(results)
    report["rankings"] = [
        {
            "rank": r.rank,
            "model": r.model_name,
            "overall_score": r.overall_score,
            "robustness": r.robustness_score,
        }
        for r in rankings
    ]
    
    # Generate vulnerability heatmap
    heatmap = generate_vulnerability_heatmap(results, attack_types)
    report["vulnerability_heatmap"] = {
        "rows": heatmap.rows,
        "columns": heatmap.columns,
        "cells": [
            {
                "attack_type": cell.attack_type,
                "metric": cell.metric,
                "value": cell.value,
            }
            for cell in heatmap.cells
        ],
    }
    
    # Pairwise comparisons
    if len(results) >= 2:
        comparisons = []
        for i in range(len(results)):
            for j in range(i + 1, len(results)):
                comparison = compare_models(results[i], results[j])
                comparisons.append(comparison)
        
        report["pairwise_comparisons"] = comparisons
    
    return report


__all__ = [
    "compare_models",
    "find_most_robust_model",
    "find_most_stable_model",
    "find_most_vulnerable_model",
    "generate_comparative_report",
    "generate_vulnerability_heatmap",
    "get_attack_type_vulnerability",
    "rank_models",
]
