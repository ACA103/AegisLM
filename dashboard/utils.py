"""
Dashboard Utilities

Utility with utils.py: functions for dashboard operations including:
- Metric calculations
- Data formatting
- Visualization helpers
- Report generation
"""

import csv
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from dashboard.schemas import (
    ComparisonData,
    DeltaRobustnessData,
    ExportFormat,
    ExportReport,
    HeatmapData,
    MetricSummary,
    RadarData,
    RunMetadata,
    RunSummary,
)

from dashboard.integrity import (
    DEFAULT_WEIGHTS,
    IntegrityValidator,
    generate_report_id,
    log_dashboard_event as log_export_event,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Metric Calculations
# =============================================================================


def calculate_vulnerability_index(
    hallucination: float,
    toxicity: float,
    bias: float,
) -> float:
    """
    Calculate vulnerability index from metrics.
    
    Higher values indicate more vulnerability.
    
    Args:
        hallucination: Mean hallucination score
        toxicity: Mean toxicity score
        bias: Mean bias score
        
    Returns:
        Vulnerability index [0, 1]
    """
    return (hallucination + toxicity + bias) / 3.0


def calculate_delta_robustness(
    baseline_score: float,
    current_score: float,
) -> float:
    """
    Calculate delta robustness between two scores.
    
    Args:
        baseline_score: Baseline composite score
        current_score: Current composite score
        
    Returns:
        Delta robustness score
    """
    return current_score - baseline_score


def normalize_metrics(
    metrics: Dict[str, float],
) -> Dict[str, float]:
    """
    Normalize metrics to [0, 1] range.
    
    Args:
        metrics: Dictionary of metric name to value
        
    Returns:
        Dictionary of normalized metrics
    """
    normalized = {}
    for name, value in metrics.items():
        # Clamp to [0, 1]
        normalized[name] = max(0.0, min(1.0, value))
    return normalized


# =============================================================================
# Data Formatting
# =============================================================================


def format_score(score: Optional[float], precision: int = 4) -> str:
    """
    Format a score for display.
    
    Args:
        score: Score value
        precision: Decimal precision
        
    Returns:
        Formatted score string
    """
    if score is None:
        return "N/A"
    return f"{score:.{precision}f}"


def format_percentage(value: float, precision: int = 2) -> str:
    """
    Format a value as percentage.
    
    Args:
        value: Value in [0, 1] range
        precision: Decimal precision
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{precision}f}%"


def format_timestamp(dt: datetime) -> str:
    """
    Format timestamp for display.
    
    Args:
        dt: Datetime object
        
    Returns:
        Formatted timestamp string
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_duration(milliseconds: float) -> str:
    """
    Format duration in milliseconds to human readable string.
    
    Args:
        milliseconds: Duration in milliseconds
        
    Returns:
        Formatted duration string
    """
    if milliseconds < 1000:
        return f"{milliseconds:.0f}ms"
    elif milliseconds < 60000:
        return f"{milliseconds / 1000:.1f}s"
    else:
        minutes = int(milliseconds / 60000)
        seconds = (milliseconds % 60000) / 1000
        return f"{minutes}m {seconds:.0f}s"


# =============================================================================
# Visualization Helpers
# =============================================================================


def get_radar_chart_config(
    radar_data: RadarData,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Plotly configuration for radar chart.
    
    Args:
        radar_data: Radar data
        title: Optional chart title
        
    Returns:
        Plotly figure configuration dictionary
    """
    return {
        "data": [
            {
                "type": "scatterpolar",
                "r": [
                    radar_data.hallucination,
                    radar_data.toxicity,
                    radar_data.bias,
                    radar_data.confidence,
                ],
                "theta": [
                    "1 - Hallucination",
                    "1 - Toxicity",
                    "1 - Bias",
                    "Confidence",
                ],
                "fill": "toself",
                "name": radar_data.model_name or "Model",
            }
        ],
        "layout": {
            "title": title or f"Robustness Radar - {radar_data.model_name or 'Model'}",
            "polar": {
                "radialaxis": {
                    "visible": True,
                    "range": [0, 1],
                    "title": "Score (higher is better)",
                }
            },
            "showlegend": True,
        },
    }


def get_heatmap_config(
    heatmap_data: HeatmapData,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Plotly configuration for heatmap.
    
    Args:
        heatmap_data: Heatmap data
        title: Optional chart title
        
    Returns:
        Plotly figure configuration dictionary
    """
    return {
        "data": [
            {
                "type": "heatmap",
                "z": heatmap_data.values,
                "x": heatmap_data.metrics,
                "y": heatmap_data.attack_types,
                "colorscale": "RdYlGn_r",  # Red (high) to Green (low)
                "zmin": 0,
                "zmax": 1,
                "colorbar": {
                    "title": "Metric Value",
                    "titleside": "right",
                },
            }
        ],
        "layout": {
            "title": title or "Attack Vulnerability Heatmap",
            "xaxis": {"title": "Metrics"},
            "yaxis": {"title": "Attack Types", "autorange": "reversed"},
        },
    }


def get_delta_chart_config(
    delta_data: List[DeltaRobustnessData],
    title: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get Plotly configuration for delta robustness bar chart.
    
    Args:
        delta_data: List of delta robustness data
        title: Optional chart title
        
    Returns:
        Plotly figure configuration dictionary
    """
    models = [d.model_name for d in delta_data]
    deltas = [d.delta_robustness for d in delta_data]
    composites = [d.composite_score for d in delta_data]
    
    # Color based on delta (green for positive, red for negative)
    colors = ["#22c55e" if d >= 0 else "#ef4444" for d in deltas]
    
    return {
        "data": [
            {
                "type": "bar",
                "x": models,
                "y": deltas,
                "marker": {"color": colors},
                "text": [f"Δ={c:.3f}" for c in composites],
                "textposition": "auto",
            }
        ],
        "layout": {
            "title": title or "Delta Robustness Comparison",
            "xaxis": {"title": "Model"},
            "yaxis": {"title": "Delta Robustness", "range": [-1, 1]},
        },
    }


# =============================================================================
# Report Generation
# =============================================================================


def generate_json_report(
    run_summary: RunSummary,
    include_config: bool = True,
    include_raw_outputs: bool = False,
) -> Dict[str, Any]:
    """
    Generate JSON report from run summary.
    
    Args:
        run_summary: Run summary data
        include_config: Include configuration in report
        include_raw_outputs: Include raw outputs (privacy sensitive)
        
    Returns:
        Report dictionary matching Week 3 Day 5 schema
    """
    # Generate report ID using SHA256 as per requirements
    report_id = generate_report_id(
        str(run_summary.metadata.run_id),
        datetime.utcnow()
    )
    
    # Build mean metrics dictionary
    mean_metrics = {}
    for metric in run_summary.metric_summary:
        mean_metrics[metric.metric_name] = metric.mean
    
    # Calculate delta metrics if composite score exists
    delta_metrics = {}
    if run_summary.composite_score is not None:
        # Calculate delta robustness (R_adv - R_base if available)
        # For now, we use the vulnerability index as a proxy
        delta_metrics = {
            "delta_R": -run_summary.vulnerability_index if run_summary.vulnerability_index else 0.0,
            "RSI": 1.0 - run_summary.vulnerability_index if run_summary.vulnerability_index else 1.0,
            "VI": run_summary.vulnerability_index if run_summary.vulnerability_index else 0.0
        }
    
    # Build per-attack breakdown if available
    per_attack = []
    if hasattr(run_summary, 'attack_coverage') and run_summary.attack_coverage:
        for attack_type in run_summary.attack_coverage:
            per_attack.append({
                "attack_type": attack_type,
                "hallucination": mean_metrics.get("hallucination", 0.0),
                "toxicity": mean_metrics.get("toxicity", 0.0),
                "bias": mean_metrics.get("bias", 0.0),
                "confidence": mean_metrics.get("confidence", 0.0),
                "robustness": run_summary.composite_score if run_summary.composite_score else 0.0
            })
    
    report = {
        "report_id": report_id,
        "generated_at": datetime.utcnow().isoformat(),
        "model": {
            "name": run_summary.metadata.model_name,
            "version": run_summary.metadata.model_version,
            "parameters": ""  # Parameters not available in run_summary
        },
        "dataset": {
            "name": run_summary.metadata.dataset_version,  # Using version as name
            "version": run_summary.metadata.dataset_version,
            "checksum": run_summary.metadata.config_hash  # Using config_hash as checksum proxy
        },
        "config_hash": run_summary.metadata.config_hash,
        "composite_score": run_summary.composite_score if run_summary.composite_score else 0.0,
        "mean_metrics": mean_metrics,
        "per_attack": per_attack,
        "delta_metrics": delta_metrics,
        "sample_count": run_summary.total_samples if hasattr(run_summary, 'total_samples') else 0,
        "notes": ""  # Empty notes by default
    }
    
    # Conditionally include config
    if include_config:
        report["config"] = {
            "config_hash": run_summary.metadata.config_hash,
            "weights": {
                "hallucination": 0.25,
                "toxicity": 0.25,
                "bias": 0.25,
                "confidence": 0.25,
            }
        }
    
    return report


def generate_csv_report(
    run_summary: RunSummary,
) -> str:
    """
    Generate CSV report from run summary.
    
    Args:
        run_summary: Run summary data
        
    Returns:
        CSV string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Metric",
        "Mean",
        "Std Dev",
        "Min",
        "Max",
        "Count",
    ])
    
    # Data rows
    for metric in run_summary.metric_summary:
        writer.writerow([
            metric.metric_name,
            f"{metric.mean:.6f}",
            f"{metric.std:.6f}",
            f"{metric.min:.6f}",
            f"{metric.max:.6f}",
            metric.count,
        ])
    
    # Composite score row
    if run_summary.composite_score is not None:
        writer.writerow([
            "composite_score",
            f"{run_summary.composite_score:.6f}",
            "",
            "",
            "",
            run_summary.total_samples,
        ])
    
    # Vulnerability index
    writer.writerow([
        "vulnerability_index",
        f"{run_summary.vulnerability_index:.6f}",
        "",
        "",
        "",
        "",
    ])
    
    return output.getvalue()


def export_report(
    run_summary: RunSummary,
    format: ExportFormat = ExportFormat.JSON,
    include_config: bool = True,
    include_raw_outputs: bool = False,
) -> str:
    """
    Export report in specified format.
    
    Args:
        run_summary: Run summary data
        format: Export format (JSON or CSV)
        include_config: Include configuration in report
        include_raw_outputs: Include raw outputs (privacy sensitive)
        
    Returns:
        Formatted report string
    """
    if format == ExportFormat.JSON:
        report = generate_json_report(
            run_summary,
            include_config=include_config,
            include_raw_outputs=include_raw_outputs,
        )
        return json.dumps(report, indent=2)
    elif format == ExportFormat.CSV:
        return generate_csv_report(run_summary)
    else:
        raise ValueError(f"Unsupported export format: {format}")


# =============================================================================
# Logging
# =============================================================================


def log_dashboard_event(
    event_type: str,
    run_id: Optional[str] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log dashboard usage events.
    
    Args:
        event_type: Type of event
        run_id: Optional run ID
        extra: Optional extra data
    """
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if run_id:
        log_data["run_id"] = run_id
    
    if extra:
        log_data.update(extra)
    
    logger.info(f"DASHBOARD_EVENT: {json.dumps(log_data)}")


def log_report_generated(
    report_id: str,
    run_id: str,
    format: str = "json",
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log REPORT_GENERATED event.
    
    Args:
        report_id: Generated report ID
        run_id: Associated run ID
        format: Export format (json/csv)
        extra: Optional extra data
    """
    log_data = {
        "event_type": "REPORT_GENERATED",
        "report_id": report_id,
        "run_id": run_id,
        "format": format,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if extra:
        log_data.update(extra)
    
    logger.info(f"REPORT_GENERATED: {json.dumps(log_data)}")


def log_benchmark_report_generated(
    benchmark_id: str,
    format: str = "json",
    model_count: int = 0,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Log BENCHMARK_REPORT_GENERATED event.
    
    Args:
        benchmark_id: Associated benchmark ID
        format: Export format (json/csv)
        model_count: Number of models in benchmark
        extra: Optional extra data
    """
    log_data = {
        "event_type": "BENCHMARK_REPORT_GENERATED",
        "benchmark_id": benchmark_id,
        "format": format,
        "model_count": model_count,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if extra:
        log_data.update(extra)
    
    logger.info(f"BENCHMARK_REPORT_GENERATED: {json.dumps(log_data)}")


# =============================================================================
# Validation
# =============================================================================


def validate_metric_range(value: float, metric_name: str) -> bool:
    """
    Validate metric is in [0, 1] range.
    
    Args:
        value: Metric value
        metric_name: Name of the metric
        
    Returns:
        True if valid, False otherwise
    """
    if not 0.0 <= value <= 1.0:
        logger.warning(f"Metric {metric_name} out of range: {value}")
        return False
    return True


def validate_run_data(results: List[Dict[str, Any]]) -> bool:
    """
    Validate run data has required fields.
    
    Args:
        results: List of result dictionaries
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ["hallucination", "toxicity", "bias", "confidence"]
    
    for i, result in enumerate(results):
        for field in required_fields:
            if field not in result:
                logger.warning(f"Result {i} missing field: {field}")
                return False
    
    return True


# =============================================================================
# Sample Data (for testing without DB)
# =============================================================================


def get_sample_run_summary() -> RunSummary:
    """
    Get sample run summary for testing.
    
    Returns:
        Sample RunSummary object
    """
    return RunSummary(
        metadata=RunMetadata(
            run_id="sample-run-001",
            timestamp=datetime.utcnow(),
            model_name="meta-llama/Llama-2-7b-hf",
            model_version="v1.0",
            dataset_version="v1.0",
            config_hash="abc123def456",
            status="completed",
        ),
        metric_summary=[
            MetricSummary(
                metric_name="hallucination",
                mean=0.15,
                std=0.08,
                min=0.02,
                max=0.45,
                count=100,
            ),
            MetricSummary(
                metric_name="toxicity",
                mean=0.08,
                std=0.05,
                min=0.0,
                max=0.32,
                count=100,
            ),
            MetricSummary(
                metric_name="bias",
                mean=0.12,
                std=0.06,
                min=0.01,
                max=0.28,
                count=100,
            ),
            MetricSummary(
                metric_name="confidence",
                mean=0.78,
                std=0.12,
                min=0.45,
                max=0.95,
                count=100,
            ),
        ],
        composite_score=0.7075,
        total_samples=100,
        attack_coverage=["injection", "jailbreak", "bias_trigger"],
        vulnerability_index=0.1167,
    )


def get_sample_radar_data() -> RadarData:
    """
    Get sample radar data for testing.
    
    Returns:
        Sample RadarData object
    """
    return RadarData(
        hallucination=0.85,
        toxicity=0.92,
        bias=0.88,
        confidence=0.78,
        model_name="meta-llama/Llama-2-7b-hf",
        run_id="sample-run-001",
    )


def get_sample_heatmap_data() -> HeatmapData:
    """
    Get sample heatmap data for testing.
    
    Returns:
        Sample HeatmapData object
    """
    return HeatmapData(
        attack_types=["injection", "jailbreak", "bias_trigger", "context_poison", "role_confusion", "chaining"],
        metrics=["hallucination", "toxicity", "bias", "confidence"],
        values=[
            [0.18, 0.12, 0.15, 0.75],  # injection
            [0.22, 0.15, 0.18, 0.72],  # jailbreak
            [0.14, 0.08, 0.25, 0.80],  # bias_trigger
            [0.16, 0.10, 0.12, 0.78],  # context_poison
            [0.19, 0.11, 0.14, 0.76],  # role_confusion
            [0.21, 0.13, 0.17, 0.74],  # chaining
        ],
        run_id="sample-run-001",
    )


# =============================================================================
# Benchmark Export Functions
# =============================================================================


def calculate_delta_robustness_model(baseline: float, adversarial: float) -> float:
    """
    Calculate delta robustness for a model.
    
    Args:
        baseline: Baseline robustness score
        adversarial: Adversarial robustness score
        
    Returns:
        Delta robustness (baseline - adversarial)
    """
    return baseline - adversarial


def calculate_rsi(baseline: float, adversarial: float) -> float:
    """
    Calculate Robustness Stability Index (RSI).
    
    RSI = R_adversarial / R_baseline
    
    Args:
        baseline: Baseline robustness score
        adversarial: Adversarial robustness score
        
    Returns:
        RSI value (closer to 1 = more stable)
    """
    if baseline == 0:
        return 0.0
    return adversarial / baseline


def calculate_vi(baseline: float, delta: float) -> float:
    """
    Calculate Vulnerability Index (VI).
    
    VI = Delta_R / R_baseline
    
    Args:
        baseline: Baseline robustness score
        delta: Delta robustness
        
    Returns:
        VI value (higher = more vulnerable)
    """
    if baseline == 0:
        return 0.0
    return delta / baseline


def load_benchmark_data(benchmark_id: str) -> Optional[Dict[str, Any]]:
    """
    Load benchmark data from JSON file.
    
    Args:
        benchmark_id: The benchmark identifier
        
    Returns:
        Benchmark data dictionary or None if not found
    """
    import os
    from pathlib import Path
    
    # Try multiple paths
    possible_paths = [
        Path(f"experiments/benchmarks/{benchmark_id}.json"),
        Path(f"../experiments/benchmarks/{benchmark_id}.json"),
        Path(f"../../experiments/benchmarks/{benchmark_id}.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            with open(path, "r") as f:
                return json.load(f)
    
    # Also try listing all benchmark files
    benchmarks_dir = Path("experiments/benchmarks")
    if benchmarks_dir.exists():
        for file in benchmarks_dir.glob("*.json"):
            if benchmark_id in file.stem or file.stem == benchmark_id:
                with open(file, "r") as f:
                    return json.load(f)
    
    return None


def list_available_benchmarks() -> List[Dict[str, str]]:
    """
    List all available benchmarks.
    
    Returns:
        List of benchmark info dictionaries
    """
    from pathlib import Path
    
    benchmarks = []
    benchmarks_dir = Path("experiments/benchmarks")
    
    if benchmarks_dir.exists():
        for file in benchmarks_dir.glob("*.json"):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    benchmarks.append({
                        "id": file.stem,
                        "name": data.get("metadata", {}).get("name", file.stem),
                        "timestamp": data.get("metadata", {}).get("timestamp", ""),
                    })
            except Exception:
                continue
    
    return benchmarks


def generate_benchmark_report(
    benchmark_data: Dict[str, Any],
    include_rankings: bool = True,
    include_comparisons: bool = True,
) -> Dict[str, Any]:
    """
    Generate benchmark report with rankings, delta_R, RSI, VI.
    
    Args:
        benchmark_data: Raw benchmark data from JSON
        include_rankings: Include model rankings
        include_comparisons: Include pairwise comparisons
        
    Returns:
        Processed benchmark report dictionary
    """
    models = benchmark_data.get("models", [])
    metadata = benchmark_data.get("metadata", {})
    
    # Process each model
    processed_models = []
    for model in models:
        baseline = model.get("baseline_robustness", 0.0)
        adversarial = model.get("adversarial_robustness", 0.0)
        
        # Calculate metrics
        delta_r = calculate_delta_robustness_model(baseline, adversarial)
        rsi = calculate_rsi(baseline, adversarial)
        vi = calculate_vi(baseline, delta_r)
        
        processed_models.append({
            "model_name": model.get("model_name", "unknown"),
            "baseline_robustness": baseline,
            "adversarial_robustness": adversarial,
            "delta_R": delta_r,
            "RSI": rsi,
            "VI": vi,
            "sample_count": model.get("sample_count", 0),
        })
    
    # Sort by adversarial robustness (descending), then by VI (ascending)
    processed_models.sort(key=lambda x: (-x["adversarial_robustness"], x["VI"]))
    
    # Add rankings
    for i, model in enumerate(processed_models):
        model["rank"] = i + 1
    
    # Find best and worst
    best_model = processed_models[0] if processed_models else None
    worst_model = processed_models[-1] if processed_models else None
    
    # Find most vulnerable (highest VI)
    most_vulnerable = max(processed_models, key=lambda x: x["VI"]) if processed_models else None
    
    # Find most stable (highest RSI)
    most_stable = max(processed_models, key=lambda x: x["RSI"]) if processed_models else None
    
    report = {
        "benchmark_id": metadata.get("name", "unknown"),
        "generated_at": datetime.utcnow().isoformat(),
        "metadata": metadata,
        "models": processed_models,
        "ranking_order": [m["model_name"] for m in processed_models],
        "best_model": best_model["model_name"] if best_model else None,
        "most_vulnerable_model": most_vulnerable["model_name"] if most_vulnerable else None,
        "most_stable_model": most_stable["model_name"] if most_stable else None,
        "summary": {
            "total_models": len(processed_models),
            "average_baseline": sum(m["baseline_robustness"] for m in processed_models) / len(processed_models) if processed_models else 0,
            "average_adversarial": sum(m["adversarial_robustness"] for m in processed_models) / len(processed_models) if processed_models else 0,
            "average_delta_R": sum(m["delta_R"] for m in processed_models) / len(processed_models) if processed_models else 0,
            "average_RSI": sum(m["RSI"] for m in processed_models) / len(processed_models) if processed_models else 0,
            "average_VI": sum(m["VI"] for m in processed_models) / len(processed_models) if processed_models else 0,
        },
    }
    
    return report


def export_benchmark_report(
    benchmark_id: str,
    format: ExportFormat = ExportFormat.JSON,
    include_rankings: bool = True,
    include_comparisons: bool = False,
) -> str:
    """
    Export benchmark report in specified format.
    
    Args:
        benchmark_id: The benchmark identifier
        format: Export format (JSON or CSV)
        include_rankings: Include rankings in report
        include_comparisons: Include pairwise comparisons
        
    Returns:
        Formatted report string
    """
    # Load benchmark data
    benchmark_data = load_benchmark_data(benchmark_id)
    
    if benchmark_data is None:
        raise ValueError(f"Benchmark not found: {benchmark_id}")
    
    # Generate report
    report = generate_benchmark_report(
        benchmark_data,
        include_rankings=include_rankings,
        include_comparisons=include_comparisons,
    )
    
    if format == ExportFormat.JSON:
        return json.dumps(report, indent=2)
    elif format == ExportFormat.CSV:
        return generate_benchmark_csv_report(report)
    else:
        raise ValueError(f"Unsupported format: {format}")


def generate_benchmark_csv_report(report: Dict[str, Any]) -> str:
    """
    Generate CSV report from benchmark report.
    
    Args:
        report: Benchmark report dictionary
        
    Returns:
        CSV string
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        "Rank",
        "Model",
        "Baseline",
        "Adversarial",
        "Delta_R",
        "RSI",
        "VI",
        "Samples",
    ])
    
    # Data rows
    for model in report.get("models", []):
        writer.writerow([
            model.get("rank", ""),
            model.get("model_name", ""),
            f"{model.get('baseline_robustness', 0):.6f}",
            f"{model.get('adversarial_robustness', 0):.6f}",
            f"{model.get('delta_R', 0):.6f}",
            f"{model.get('RSI', 0):.6f}",
            f"{model.get('VI', 0):.6f}",
            model.get("sample_count", ""),
        ])
    
    # Summary rows
    writer.writerow([])
    writer.writerow(["Summary"])
    summary = report.get("summary", {})
    writer.writerow(["Total Models", summary.get("total_models", 0)])
    writer.writerow(["Average Baseline", f"{summary.get('average_baseline', 0):.6f}"])
    writer.writerow(["Average Adversarial", f"{summary.get('average_adversarial', 0):.6f}"])
    writer.writerow(["Average Delta_R", f"{summary.get('average_delta_R', 0):.6f}"])
    writer.writerow(["Average RSI", f"{summary.get('average_RSI', 0):.6f}"])
    writer.writerow(["Average VI", f"{summary.get('average_VI', 0):.6f}"])
    
    writer.writerow([])
    writer.writerow(["Best Model", report.get("best_model", "N/A")])
    writer.writerow(["Most Vulnerable", report.get("most_vulnerable_model", "N/A")])
    writer.writerow(["Most Stable", report.get("most_stable_model", "N/A")])
    
    return output.getvalue()


def save_benchmark_report(
    benchmark_id: str,
    report: Dict[str, Any],
    output_dir: str = "reports",
) -> str:
    """
    Save benchmark report to file.
    
    Args:
        benchmark_id: The benchmark identifier
        report: Report dictionary
        output_dir: Output directory
        
    Returns:
        Path to saved file
    """
    import os
    from pathlib import Path
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Generate filename
    filename = f"benchmark_{benchmark_id}.json"
    filepath = output_path / filename
    
    # Write file
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    
    return str(filepath)
