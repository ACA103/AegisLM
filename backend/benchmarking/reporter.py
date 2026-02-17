"""
Benchmark Reporter Module

Handles benchmark artifact generation and reporting:
- JSON artifact structure
- Report generation
- File I/O operations
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.benchmarking.schemas import (
    BenchmarkResult,
    BenchmarkStatus,
)


# =============================================================================
# Configuration
# =============================================================================

DEFAULT_BENCHMARK_DIR = "experiments/benchmarks"


# =============================================================================
# Artifact Generation
# =============================================================================

def generate_benchmark_artifact(
    result: BenchmarkResult,
    output_dir: Optional[str] = None,
) -> str:
    """
    Generate benchmark artifact JSON file.
    
    Args:
        result: Complete benchmark result
        output_dir: Optional output directory (defaults to experiments/benchmarks)
    
    Returns:
        Path to the generated artifact file
    """
    if output_dir is None:
        output_dir = DEFAULT_BENCHMARK_DIR
    
    # Create output directory if it doesn't exist
    artifact_dir = Path(output_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"{result.benchmark_id}.json"
    artifact_path = artifact_dir / filename
    
    # Convert result to dictionary
    artifact_data = result_to_dict(result)
    
    # Write to file
    with open(artifact_path, "w") as f:
        json.dump(artifact_data, f, indent=2, default=str)
    
    return str(artifact_path)


def result_to_dict(result: BenchmarkResult) -> Dict[str, Any]:
    """
    Convert BenchmarkResult to dictionary for JSON serialization.
    
    Args:
        result: BenchmarkResult to convert
    
    Returns:
        Dictionary representation
    """
    data = {
        "benchmark_id": str(result.benchmark_id),
        "dataset_name": result.dataset_name,
        "dataset_version": result.dataset_version,
        "models": result.models,
        "status": result.status.value,
        "started_at": result.started_at.isoformat() if result.started_at else None,
        "completed_at": result.completed_at.isoformat() if result.completed_at else None,
        "error": result.error,
    }
    
    # Add results per model
    results_list = []
    for model_result in result.results:
        model_data = {
            "model_name": model_result.model_name,
            "baseline_robustness": model_result.baseline_robustness,
            "adversarial_robustness": model_result.adversarial_robustness,
            "delta_robustness": model_result.delta_robustness,
            "robustness_stability_index": model_result.robustness_stability_index,
            "vulnerability_index": model_result.vulnerability_index,
        }
        
        # Add baseline metrics
        if model_result.baseline:
            model_data["baseline"] = {
                "mode": model_result.baseline.mode.value,
                "sample_count": model_result.baseline.sample_count,
                "failure_rate": model_result.baseline.failure_rate,
                "metrics": model_result.baseline.metrics.model_dump() if model_result.baseline.metrics else None,
                "mean_latency_ms": model_result.baseline.mean_latency_ms,
                "total_time_seconds": model_result.baseline.total_time_seconds,
                "timestamp": model_result.baseline.timestamp.isoformat() if model_result.baseline.timestamp else None,
            }
        
        # Add adversarial metrics
        if model_result.adversarial:
            model_data["adversarial"] = {
                "mode": model_result.adversarial.mode.value,
                "sample_count": model_result.adversarial.sample_count,
                "failure_rate": model_result.adversarial.failure_rate,
                "metrics": model_result.adversarial.metrics.model_dump() if model_result.adversarial.metrics else None,
                "mean_latency_ms": model_result.adversarial.mean_latency_ms,
                "total_time_seconds": model_result.adversarial.total_time_seconds,
                "timestamp": model_result.adversarial.timestamp.isoformat() if model_result.adversarial.timestamp else None,
            }
        
        # Add deltas
        if model_result.deltas:
            model_data["deltas"] = model_result.deltas.model_dump()
        
        results_list.append(model_data)
    
    data["results"] = results_list
    
    # Add rankings
    if result.rankings:
        data["rankings"] = [
            ranking.model_dump() for ranking in result.rankings
        ]
    
    # Add vulnerability heatmap
    if result.vulnerability_heatmap:
        data["vulnerability_heatmap"] = {
            "rows": result.vulnerability_heatmap.rows,
            "columns": result.vulnerability_heatmap.columns,
            "cells": [
                cell.model_dump() for cell in result.vulnerability_heatmap.cells
            ],
        }
    
    # Add performance tracking
    data["performance"] = {
        "time_per_model_seconds": result.performance.time_per_model_seconds,
        "gpu_memory_mb": result.performance.gpu_memory_mb,
        "sample_counts": result.performance.sample_counts,
        "failure_rates": result.performance.failure_rates,
    }
    
    # Add config
    if result.config:
        data["config"] = result.config
    
    return data


# =============================================================================
# Report Generation
# =============================================================================

def generate_text_report(result: BenchmarkResult) -> str:
    """
    Generate human-readable text report.
    
    Args:
        result: BenchmarkResult to report
    
    Returns:
        Formatted text report
    """
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append(f"AEGISLM BENCHMARK REPORT")
    lines.append("=" * 60)
    lines.append(f"Benchmark ID: {result.benchmark_id}")
    lines.append(f"Status: {result.status.value}")
    lines.append(f"Dataset: {result.dataset_name} ({result.dataset_version})")
    lines.append(f"Models Evaluated: {', '.join(result.models)}")
    lines.append("")
    
    # Timing
    lines.append(f"Started: {result.started_at.isoformat() if result.started_at else 'N/A'}")
    if result.completed_at:
        duration = (result.completed_at - result.started_at).total_seconds() if result.started_at else 0
        lines.append(f"Completed: {result.completed_at.isoformat()}")
        lines.append(f"Duration: {duration:.2f} seconds")
    lines.append("")
    
    # Results per model
    lines.append("-" * 60)
    lines.append("MODEL RESULTS")
    lines.append("-" * 60)
    
    for model_result in result.results:
        lines.append(f"\nModel: {model_result.model_name}")
        
        if model_result.baseline:
            lines.append(f"  Baseline Robustness: {model_result.baseline_robustness:.4f}" if model_result.baseline_robustness else "  Baseline: N/A")
        
        if model_result.adversarial:
            lines.append(f"  Adversarial Robustness: {model_result.adversarial_robustness:.4f}" if model_result.adversarial_robustness else "  Adversarial: N/A")
        
        if model_result.delta_robustness is not None:
            lines.append(f"  Delta Robustness: {model_result.delta_robustness:.4f}")
        
        if model_result.robustness_stability_index is not None:
            lines.append(f"  Robustness Stability Index (RSI): {model_result.robustness_stability_index:.4f}")
        
        if model_result.vulnerability_index is not None:
            lines.append(f"  Vulnerability Index: {model_result.vulnerability_index:.4f}")
    
    # Rankings
    if result.rankings:
        lines.append("")
        lines.append("-" * 60)
        lines.append("MODEL RANKINGS")
        lines.append("-" * 60)
        
        for ranking in result.rankings:
            lines.append(f"  {ranking.rank}. {ranking.model_name} (Score: {ranking.overall_score:.4f})")
    
    # Performance
    lines.append("")
    lines.append("-" * 60)
    lines.append("PERFORMANCE")
    lines.append("-" * 60)
    
    for model_name, time_seconds in result.performance.time_per_model_seconds.items():
        lines.append(f"  {model_name}: {time_seconds:.2f} seconds")
    
    # Error
    if result.error:
        lines.append("")
        lines.append("-" * 60)
        lines.append("ERROR")
        lines.append("-" * 60)
        lines.append(f"  {result.error}")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


def generate_summary_report(result: BenchmarkResult) -> Dict[str, Any]:
    """
    Generate summary report as dictionary.
    
    Args:
        result: BenchmarkResult to summarize
    
    Returns:
        Summary dictionary
    """
    summary = {
        "benchmark_id": str(result.benchmark_id),
        "status": result.status.value,
        "dataset": f"{result.dataset_name} ({result.dataset_version})",
        "total_models": len(result.models),
        "successful_evaluations": len([r for r in result.results if r.adversarial is not None]),
    }
    
    # Find best and worst
    valid_results = [r for r in result.results if r.adversarial_robustness is not None]
    
    if valid_results:
        best = max(valid_results, key=lambda x: x.adversarial_robustness)
        worst = min(valid_results, key=lambda x: x.adversarial_robustness)
        
        summary["best_model"] = {
            "name": best.model_name,
            "robustness": best.adversarial_robustness,
        }
        
        summary["worst_model"] = {
            "name": worst.model_name,
            "robustness": worst.adversarial_robustness,
        }
        
        # Average robustness
        avg_robustness = sum(r.adversarial_robustness for r in valid_results) / len(valid_results)
        summary["average_robustness"] = avg_robustness
    
    # Rankings summary
    if result.rankings and result.rankings:
        summary["top_model"] = result.rankings[0].model_name
        summary["top_score"] = result.rankings[0].overall_score
    
    return summary


# =============================================================================
# Artifact Loading
# =============================================================================

def load_benchmark_artifact(
    benchmark_id: str,
    input_dir: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Load benchmark artifact from file.
    
    Args:
        benchmark_id: The benchmark ID to load
        input_dir: Optional input directory
    
    Returns:
        Dictionary representation of the benchmark, or None if not found
    """
    if input_dir is None:
        input_dir = DEFAULT_BENCHMARK_DIR
    
    artifact_path = Path(input_dir) / f"{benchmark_id}.json"
    
    if not artifact_path.exists():
        return None
    
    with open(artifact_path, "r") as f:
        return json.load(f)


def list_benchmarks(
    input_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List all available benchmarks.
    
    Args:
        input_dir: Optional input directory
    
    Returns:
        List of benchmark summaries
    """
    if input_dir is None:
        input_dir = DEFAULT_BENCHMARK_DIR
    
    benchmark_dir = Path(input_dir)
    
    if not benchmark_dir.exists():
        return []
    
    benchmarks = []
    
    for artifact_file in benchmark_dir.glob("*.json"):
        try:
            with open(artifact_file, "r") as f:
                data = json.load(f)
                benchmarks.append({
                    "benchmark_id": data.get("benchmark_id"),
                    "status": data.get("status"),
                    "dataset": f"{data.get('dataset_name')} ({data.get('dataset_version')})",
                    "models": data.get("models", []),
                    "started_at": data.get("started_at"),
                    "completed_at": data.get("completed_at"),
                })
        except Exception:
            continue
    
    # Sort by started_at (newest first)
    benchmarks.sort(key=lambda x: x.get("started_at", ""), reverse=True)
    
    return benchmarks


# =============================================================================
# Export Functions
# =============================================================================

def export_to_csv(
    result: BenchmarkResult,
    output_path: str,
) -> None:
    """
    Export benchmark results to CSV.
    
    Args:
        result: BenchmarkResult to export
        output_path: Path to output CSV file
    """
    import csv
    
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow([
            "Model",
            "Baseline Robustness",
            "Adversarial Robustness",
            "Delta Robustness",
            "RSI",
            "Vulnerability Index",
            "Hallucination Delta",
            "Toxicity Delta",
            "Bias Delta",
            "Confidence Delta",
        ])
        
        # Data rows
        for model_result in result.results:
            writer.writerow([
                model_result.model_name,
                model_result.baseline_robustness or "",
                model_result.adversarial_robustness or "",
                model_result.delta_robustness or "",
                model_result.robustness_stability_index or "",
                model_result.vulnerability_index or "",
                model_result.deltas.hallucination_delta if model_result.deltas else "",
                model_result.deltas.toxicity_delta if model_result.deltas else "",
                model_result.deltas.bias_delta if model_result.deltas else "",
                model_result.deltas.confidence_delta if model_result.deltas else "",
            ])


__all__ = [
    "DEFAULT_BENCHMARK_DIR",
    "generate_benchmark_artifact",
    "generate_text_report",
    "generate_summary_report",
    "load_benchmark_artifact",
    "list_benchmarks",
    "export_to_csv",
]
