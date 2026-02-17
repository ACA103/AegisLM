"""
Dashboard Data Loader

Handles data retrieval from the backend database and transforms
data into chart-ready formats for dashboard visualization.

This layer abstracts database queries and provides clean interfaces
for the visualization components.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from backend.scoring.aggregator import ScoreAggregator

import json
from pathlib import Path

from dashboard.schemas import (
    AttackBreakdown,
    AttackBreakdownList,
    BenchmarkComparisonData,
    BenchmarkInfo,
    BenchmarkStats,
    ComparisonData,
    DeltaRobustnessData,
    HeatmapData,
    MetricSummary,
    RadarData,
    RunMetadata,
    RunSummary,
)

logger = logging.getLogger(__name__)


# Sample data for demo mode
SAMPLE_RUNS = [
    {
        "id": "sample-run-001",
        "model_name": "gpt-4",
        "model_version": "v1.0",
        "dataset_version": "v1.0",
        "timestamp": "2024-01-15T10:30:00Z",
        "status": "completed",
        "composite_score": 0.75,
    },
    {
        "id": "sample-run-002", 
        "model_name": "claude-3",
        "model_version": "v1.0",
        "dataset_version": "v1.0",
        "timestamp": "2024-01-16T14:20:00Z",
        "status": "completed",
        "composite_score": 0.82,
    },
]


def _get_sample_results(run_id: str) -> List[Dict[str, Any]]:
    """Generate sample results for demo mode."""
    import random
    
    # Handle case where run_id might be a list (from Gradio dropdown)
    if isinstance(run_id, list):
        run_id = run_id[0] if run_id else "default"
    
    # Convert to string if not already
    run_id = str(run_id)
    
    random.seed(hash(run_id) % 10000)
    
    attack_types = ["injection", "jailbreak", "bias_trigger", "context_poison", "role_confusion"]
    results = []
    
    for i in range(20):
        results.append({
            "id": f"{run_id}-result-{i}",
            "sample_id": f"sample-{i}",
            "attack_type": random.choice(attack_types) if i % 2 == 0 else None,
            "mutation_type": "paraphrase" if i % 3 == 0 else None,
            "hallucination": random.uniform(0.05, 0.35),
            "toxicity": random.uniform(0.02, 0.15),
            "bias": random.uniform(0.05, 0.25),
            "confidence": random.uniform(0.60, 0.90),
            "robustness": random.uniform(0.50, 0.85),
        })
    
    return results


class DashboardDataLoader:
    """
    Data loader for dashboard visualization.
    
    Responsibilities:
    - Fetch evaluation runs
    - Fetch evaluation results
    - Fetch benchmark artifacts
    - Transform data into chart-ready format
    
    Note: Communicates with backend via internal function calls (same container).
    No direct DB exposure to frontend.
    """

    def __init__(self, demo_mode: bool = True):
        """
        Initialize data loader.
        
        Args:
            demo_mode: If True, return sample data without database
        """
        self._demo_mode = demo_mode
        self._aggregator = ScoreAggregator()

    # =========================================================================
    # Run Retrieval - SYNCHRONOUS
    # =========================================================================

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """
        Get all evaluation runs.
        
        Returns:
            List of run dictionaries with id, model_name, timestamp, status
        """
        if self._demo_mode:
            return SAMPLE_RUNS
        
        # Try to read from benchmark files
        runs = []
        runs_dir = Path("experiments/runs")
        
        if runs_dir.exists():
            for run_file in runs_dir.glob("*.json"):
                try:
                    with open(run_file, "r") as f:
                        run_data = json.load(f)
                        runs.append({
                            "id": run_data.get("run_id", run_file.stem),
                            "model_name": run_data.get("model_name", "unknown"),
                            "model_version": run_data.get("model_version", "v1.0"),
                            "dataset_version": run_data.get("dataset_version", "v1.0"),
                            "timestamp": run_data.get("timestamp", ""),
                            "status": run_data.get("status", "completed"),
                            "composite_score": run_data.get("composite_score"),
                        })
                except Exception as e:
                    logger.error(f"Error loading run {run_file}: {e}")
        
        return runs if runs else SAMPLE_RUNS

    def get_run_by_id(self, run_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific run by ID."""
        if self._demo_mode:
            for run in SAMPLE_RUNS:
                if run["id"] == run_id:
                    return run
            return SAMPLE_RUNS[0] if SAMPLE_RUNS else None
        
        return None

    def get_run_results(self, run_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get results for a run."""
        if self._demo_mode:
            results = _get_sample_results(run_id)
            return results[:limit] if limit else results
        return []

    # =========================================================================
    # Run Summary - SYNCHRONOUS
    # =========================================================================

    def get_run_summary(self, run_id: str) -> Optional[RunSummary]:
        """Get complete summary for a run."""
        run_data = self.get_run_by_id(run_id)
        if run_data is None:
            return None
        
        results = self.get_run_results(run_id)
        
        if not results:
            return None
        
        # Calculate metrics
        hallucinations = [r["hallucination"] for r in results if r["hallucination"] is not None]
        toxicities = [r["toxicity"] for r in results if r["toxicity"] is not None]
        biases = [r["bias"] for r in results if r["bias"] is not None]
        confidences = [r["confidence"] for r in results if r["confidence"] is not None]
        
        # Get attack coverage
        attack_types = set()
        for r in results:
            if r.get("attack_type"):
                attack_types.add(r["attack_type"])
        
        # Calculate metric summaries
        metric_summaries = []
        
        if hallucinations:
            metric_summaries.append(MetricSummary.from_values("hallucination", hallucinations))
        if toxicities:
            metric_summaries.append(MetricSummary.from_values("toxicity", toxicities))
        if biases:
            metric_summaries.append(MetricSummary.from_values("bias", biases))
        if confidences:
            metric_summaries.append(MetricSummary.from_values("confidence", confidences))
        
        # Calculate composite score from means
        composite_score = None
        if hallucinations and toxicities and biases and confidences:
            mean_h = sum(hallucinations) / len(hallucinations)
            mean_t = sum(toxicities) / len(toxicities)
            mean_b = sum(biases) / len(biases)
            mean_c = sum(confidences) / len(confidences)
            composite_score = self._aggregator.calculate_composite(
                mean_h, mean_t, mean_b, mean_c
            )
        
        # Calculate vulnerability index
        vulnerability_index = RunSummary.calculate_vulnerability_index(
            mean_h if hallucinations else 0.0,
            mean_t if toxicities else 0.0,
            mean_b if biases else 0.0,
        )
        
        # Build metadata
        from datetime import datetime
        
        metadata = RunMetadata(
            run_id=run_data["id"],
            timestamp=datetime.fromisoformat(run_data["timestamp"].replace("Z", "+00:00")) if run_data.get("timestamp") else datetime.utcnow(),
            model_name=run_data["model_name"],
            model_version=run_data["model_version"],
            dataset_version=run_data["dataset_version"],
            config_hash="demo_hash",
            status=run_data["status"],
        )
        
        return RunSummary(
            metadata=metadata,
            metric_summary=metric_summaries,
            composite_score=composite_score,
            total_samples=len(results),
            attack_coverage=sorted(list(attack_types)),
            vulnerability_index=vulnerability_index,
        )

    # =========================================================================
    # Radar Chart Data - SYNCHRONOUS
    # =========================================================================

    def get_radar_data(self, run_id: str) -> Optional[RadarData]:
        """Get radar chart data for a run."""
        run_data = self.get_run_by_id(run_id)
        if run_data is None:
            return None
        
        results = self.get_run_results(run_id)
        
        if not results:
            return None
        
        # Calculate means
        hallucinations = [r["hallucination"] for r in results if r["hallucination"] is not None]
        toxicities = [r["toxicity"] for r in results if r["toxicity"] is not None]
        biases = [r["bias"] for r in results if r["bias"] is not None]
        confidences = [r["confidence"] for r in results if r["confidence"] is not None]
        
        if not all([hallucinations, toxicities, biases, confidences]):
            return None
        
        mean_h = sum(hallucinations) / len(hallucinations)
        mean_t = sum(toxicities) / len(toxicities)
        mean_b = sum(biases) / len(biases)
        mean_c = sum(confidences) / len(confidences)
        
        return RadarData.from_metrics(
            mean_hallucination=mean_h,
            mean_toxicity=mean_t,
            mean_bias=mean_b,
            mean_confidence=mean_c,
            model_name=run_data["model_name"],
            run_id=run_id,
        )

    # =========================================================================
    # Heatmap Data - SYNCHRONOUS
    # =========================================================================

    def get_attack_heatmap(self, run_id: str) -> Optional[HeatmapData]:
        """Get attack vulnerability heatmap data."""
        results = self.get_run_results(run_id)
        
        if not results:
            return None
        
        # Convert to dict format for from_results
        heatmap_data = HeatmapData.from_results(results)
        heatmap_data.run_id = run_id
        return heatmap_data

    # =========================================================================
    # Attack Breakdown - SYNCHRONOUS
    # =========================================================================

    def get_attack_breakdown(self, run_id: str) -> Optional[AttackBreakdownList]:
        """Get per-attack metric breakdown data."""
        results = self.get_run_results(run_id)
        
        if not results:
            return None
        
        # Create breakdown list
        breakdown_list = AttackBreakdownList.from_results(results, run_id=run_id)
        return breakdown_list

    def get_attack_types_for_run(self, run_id: str) -> List[str]:
        """Get list of attack types for a run."""
        results = self.get_run_results(run_id)
        
        if not results:
            return []
        
        attack_types = set()
        for result in results:
            attack_type = result.get("attack_type") or "none"
            attack_types.add(attack_type)
        
        return sorted(list(attack_types))

    # =========================================================================
    # Model Comparison - SYNCHRONOUS
    # =========================================================================

    def get_model_comparison(self, run_ids: List[str]) -> Optional[ComparisonData]:
        """Get comparison data for multiple runs."""
        if not run_ids or len(run_ids) < 2:
            return None
        
        models = []
        hallucination_scores = []
        toxicity_scores = []
        bias_scores = []
        confidence_scores = []
        composite_scores = []
        sample_counts = []
        
        for run_id in run_ids:
            run_data = self.get_run_by_id(run_id)
            if run_data is None:
                continue
            
            results = self.get_run_results(run_id)
            if not results:
                continue
            
            models.append(run_data["model_name"])
            
            # Calculate means
            hallucinations = [r["hallucination"] for r in results if r["hallucination"] is not None]
            toxicities = [r["toxicity"] for r in results if r["toxicity"] is not None]
            biases = [r["bias"] for r in results if r["bias"] is not None]
            confidences = [r["confidence"] for r in results if r["confidence"] is not None]
            
            mean_h = sum(hallucinations) / len(hallucinations) if hallucinations else 0.0
            mean_t = sum(toxicities) / len(toxicities) if toxicities else 0.0
            mean_b = sum(biases) / len(biases) if biases else 0.0
            mean_c = sum(confidences) / len(confidences) if confidences else 0.0
            
            hallucination_scores.append(mean_h)
            toxicity_scores.append(mean_t)
            bias_scores.append(mean_b)
            confidence_scores.append(mean_c)
            
            # Calculate composite
            composite = self._aggregator.calculate_composite(mean_h, mean_t, mean_b, mean_c)
            composite_scores.append(composite)
            
            sample_counts.append(len(results))
        
        if len(models) < 2:
            return None
        
        return ComparisonData(
            models=models,
            hallucination=hallucination_scores,
            toxicity=toxicity_scores,
            bias=bias_scores,
            confidence=confidence_scores,
            composite_score=composite_scores,
            sample_count=sample_counts,
        )

    def get_delta_robustness(self, run_ids: List[str]) -> List[DeltaRobustnessData]:
        """Get delta robustness comparison for multiple runs."""
        comparison = self.get_model_comparison(run_ids)
        
        if comparison is None:
            return []
        
        # Find baseline (first model or lowest composite)
        baseline_score = min(comparison.composite_score)
        
        deltas = []
        for i, model in enumerate(comparison.models):
            delta = comparison.composite_score[i] - baseline_score
            deltas.append(
                DeltaRobustnessData(
                    model_name=model,
                    delta_robustness=delta,
                    composite_score=comparison.composite_score[i],
                    rank=i + 1,
                )
            )
        
        # Sort by composite score descending
        deltas.sort(key=lambda x: x.composite_score, reverse=True)
        
        # Update ranks
        for i, delta in enumerate(deltas):
            delta.rank = i + 1
        
        return deltas

    # =========================================================================
    # Benchmark Artifacts - SYNCHRONOUS
    # =========================================================================

    def _get_benchmark_path(self, benchmark_id: str) -> Path:
        """Get the file path for a benchmark artifact."""
        base_dir = Path("experiments/benchmarks")
        return base_dir / f"{benchmark_id}.json"

    def list_benchmarks(self) -> List[BenchmarkInfo]:
        """List all available benchmarks."""
        benchmarks = []
        base_dir = Path("experiments/benchmarks")
        
        if not base_dir.exists():
            logger.warning(f"Benchmarks directory does not exist: {base_dir}")
            return benchmarks
        
        # Find all JSON files in the benchmarks directory
        for json_file in base_dir.glob("*.json"):
            benchmark_id = json_file.stem
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                
                info = BenchmarkInfo.from_json(benchmark_id, data)
                benchmarks.append(info)
            except Exception as e:
                logger.error(f"Error loading benchmark {benchmark_id}: {e}")
                continue
        
        # Sort by timestamp descending (most recent first)
        benchmarks.sort(key=lambda x: x.timestamp, reverse=True)
        
        return benchmarks

    def get_benchmark_comparison(self, benchmark_id: str) -> Optional[BenchmarkComparisonData]:
        """Get benchmark comparison data for multiple models."""
        benchmark_path = self._get_benchmark_path(benchmark_id)
        
        if not benchmark_path.exists():
            logger.warning(f"Benchmark not found: {benchmark_path}")
            return None
        
        try:
            with open(benchmark_path, "r") as f:
                data = json.load(f)
            
            comparison = BenchmarkComparisonData.from_json(benchmark_id, data)
            
            # Log benchmark view
            logger.info(
                f"DASHBOARD_VIEW_BENCHMARK benchmark_id={benchmark_id} "
                f"model_count={comparison.total_models}"
            )
            
            return comparison
        except Exception as e:
            logger.error(f"Error loading benchmark {benchmark_id}: {e}")
            return None

    def get_benchmark_stats(self, benchmark_id: str) -> Optional[BenchmarkStats]:
        """Get statistical summary for a benchmark."""
        comparison = self.get_benchmark_comparison(benchmark_id)
        
        if comparison is None:
            return None
        
        stats = BenchmarkStats.from_comparison_data(benchmark_id, comparison)
        
        logger.info(
            f"DASHBOARD_COMPARE_MODELS benchmark_id={benchmark_id} "
            f"model_count={stats.total_models}"
        )
        
        return stats


# =============================================================================
# Factory Functions
# =============================================================================


def get_data_loader(demo_mode: bool = True) -> DashboardDataLoader:
    """
    Get a DashboardDataLoader instance.
    
    Args:
        demo_mode: If True, return sample data without database
        
    Returns:
        DashboardDataLoader instance
    """
    return DashboardDataLoader(demo_mode=demo_mode)
