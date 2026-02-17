"""
Dashboard Visualization Schemas

Defines Pydantic models for dashboard data visualization.
Includes schemas for radar charts, heatmaps, comparison data, and metrics.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class MetricType(str, Enum):
    """Available metric types for visualization."""

    HALLUCINATION = "hallucination"
    TOXICITY = "toxicity"
    BIAS = "bias"
    CONFIDENCE = "confidence"
    ROBUSTNESS = "robustness"


class AttackType(str, Enum):
    """Attack types for vulnerability analysis."""

    INJECTION = "injection"
    JAILBREAK = "jailbreak"
    BIAS_TRIGGER = "bias_trigger"
    CONTEXT_POISON = "context_poison"
    ROLE_CONFUSION = "role_confusion"
    CHAINING = "chaining"
    NONE = "none"


# =============================================================================
# Radar Chart Schemas
# =============================================================================


class RadarData(BaseModel):
    """
    Data schema for radar chart visualization.
    
    Each axis represents an inverse metric (higher is better):
    - 1 - Hallucination (lower hallucination = better)
    - 1 - Toxicity (lower toxicity = better)
    - 1 - Bias (lower bias = better)
    - Confidence (higher confidence = better)
    
    Formula: V = [1 - H̄, 1 - T̄, 1 - B̄, C̄]
    """

    hallucination: float = Field(
        description="1 - mean_hallucination (higher is better)",
        ge=0.0,
        le=1.0,
    )
    toxicity: float = Field(
        description="1 - mean_toxicity (higher is better)",
        ge=0.0,
        le=1.0,
    )
    bias: float = Field(
        description="1 - mean_bias (higher is better)",
        ge=0.0,
        le=1.0,
    )
    confidence: float = Field(
        description="Mean confidence score",
        ge=0.0,
        le=1.0,
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Name of the model",
    )
    run_id: Optional[str] = Field(
        default=None,
        description="Evaluation run ID",
    )

    @classmethod
    def from_metrics(
        cls,
        mean_hallucination: float,
        mean_toxicity: float,
        mean_bias: float,
        mean_confidence: float,
        model_name: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> "RadarData":
        """
        Create RadarData from mean metric values.
        
        Args:
            mean_hallucination: Mean hallucination score
            mean_toxicity: Mean toxicity score
            mean_bias: Mean bias score
            mean_confidence: Mean confidence score
            model_name: Optional model name
            run_id: Optional run ID
            
        Returns:
            RadarData instance with inverted metrics
        """
        return cls(
            hallucination=1.0 - mean_hallucination,
            toxicity=1.0 - mean_toxicity,
            bias=1.0 - mean_bias,
            confidence=mean_confidence,
            model_name=model_name,
            run_id=run_id,
        )

    def to_plotly_radar(self) -> Dict[str, Any]:
        """
        Convert to Plotly radar chart format.
        
        Returns:
            Dictionary suitable for Plotly go.Scatterpolar
        """
        return {
            "r": [
                self.hallucination,
                self.toxicity,
                self.bias,
                self.confidence,
            ],
            "theta": ["1 - Hallucination", "1 - Toxicity", "1 - Bias", "Confidence"],
            "fill": "toself",
        }


# =============================================================================
# Heatmap Schemas
# =============================================================================


class HeatmapData(BaseModel):
    """
    Data schema for attack vulnerability heatmap.
    
    Matrix format:
    - Rows = Attack Types
    - Columns = Metrics
    - Cell value = mean(metric_j | attack_i)
    
    Color coding:
    - Red → high vulnerability (high metric value = bad)
    - Green → low vulnerability (low metric value = good)
    
    Note: Uses "confidence_collapse" (1 - confidence) instead of raw confidence
    to ensure consistent direction (higher = worse = red).
    """

    attack_types: List[str] = Field(
        description="List of attack types (rows)",
    )
    metrics: List[str] = Field(
        description="List of metric names (columns)",
    )
    values: List[List[float]] = Field(
        description="2D matrix of mean metric values per attack type",
    )
    run_id: Optional[str] = Field(
        default=None,
        description="Evaluation run ID",
    )

    @classmethod
    def from_results(
        cls,
        results: List[Dict[str, Any]],
    ) -> "HeatmapData":
        """
        Create HeatmapData from evaluation results.
        
        Args:
            results: List of evaluation result dictionaries
            
        Returns:
            HeatmapData instance
        """
        # Group by attack type
        attack_metrics: Dict[str, Dict[str, List[float]]] = {}
        
        for result in results:
            attack_type = result.get("attack_type", "none") or "none"
            
            if attack_type not in attack_metrics:
                attack_metrics[attack_type] = {
                    "hallucination": [],
                    "toxicity": [],
                    "bias": [],
                    "confidence": [],
                }
            
            attack_metrics[attack_type]["hallucination"].append(
                result.get("hallucination", 0.0) or 0.0
            )
            attack_metrics[attack_type]["toxicity"].append(
                result.get("toxicity", 0.0) or 0.0
            )
            attack_metrics[attack_type]["bias"].append(
                result.get("bias", 0.0) or 0.0
            )
            attack_metrics[attack_type]["confidence"].append(
                result.get("confidence", 0.0) or 0.0
            )
        
        # Calculate means
        attack_types = sorted(attack_metrics.keys())
        # Use confidence_collapse (1 - confidence) instead of raw confidence
        metrics = ["hallucination", "toxicity", "bias", "confidence_collapse"]
        
        values = []
        for attack_type in attack_types:
            row = []
            for metric in metrics:
                if metric == "confidence_collapse":
                    # Calculate 1 - mean_confidence
                    conf_values = attack_metrics[attack_type]["confidence"]
                    mean_conf = sum(conf_values) / len(conf_values) if conf_values else 0.0
                    row.append(1.0 - mean_conf)
                else:
                    metric_values = attack_metrics[attack_type][metric]
                    mean_value = sum(metric_values) / len(metric_values) if metric_values else 0.0
                    row.append(mean_value)
            values.append(row)
        
        return cls(
            attack_types=attack_types,
            metrics=metrics,
            values=values,
        )


class AttackBreakdown(BaseModel):
    """
    Data schema for per-attack metric breakdown.
    
    Provides detailed statistics for a specific attack type including:
    - Sample count
    - Mean metrics (hallucination, toxicity, bias, confidence)
    - Robustness under this attack
    - Vulnerability index
    """

    attack_type: str = Field(
        description="Type of attack",
    )
    sample_count: int = Field(
        description="Number of samples with this attack type",
        ge=0,
    )
    mean_hallucination: float = Field(
        description="Mean hallucination score under this attack",
        ge=0.0,
        le=1.0,
    )
    mean_toxicity: float = Field(
        description="Mean toxicity score under this attack",
        ge=0.0,
        le=1.0,
    )
    mean_bias: float = Field(
        description="Mean bias score under this attack",
        ge=0.0,
        le=1.0,
    )
    mean_confidence: float = Field(
        description="Mean confidence score under this attack",
        ge=0.0,
        le=1.0,
    )
    robustness: float = Field(
        description="Robustness score under this attack (R_a)",
        ge=0.0,
        le=1.0,
    )
    vulnerability_index: float = Field(
        description="Vulnerability index for this attack (VI_a)",
        ge=0.0,
        le=1.0,
    )
    confidence_collapse: float = Field(
        description="Confidence collapse (1 - mean_confidence)",
        ge=0.0,
        le=1.0,
    )
    run_id: Optional[str] = Field(
        default=None,
        description="Evaluation run ID",
    )

    @classmethod
    def from_results(
        cls,
        results: List[Dict[str, Any]],
        attack_type: str,
        baseline_robustness: Optional[float] = None,
        run_id: Optional[str] = None,
    ) -> "AttackBreakdown":
        """
        Create AttackBreakdown from evaluation results for a specific attack type.
        
        Args:
            results: List of evaluation result dictionaries
            attack_type: The attack type to compute breakdown for
            baseline_robustness: Optional baseline robustness for VI calculation
            run_id: Optional run ID
            
        Returns:
            AttackBreakdown instance
        """
        # Filter results by attack type
        attack_results = [
            r for r in results 
            if (r.get("attack_type") or "none") == attack_type
        ]
        
        if not attack_results:
            return cls(
                attack_type=attack_type,
                sample_count=0,
                mean_hallucination=0.0,
                mean_toxicity=0.0,
                mean_bias=0.0,
                mean_confidence=0.0,
                robustness=0.0,
                vulnerability_index=0.0,
                confidence_collapse=0.0,
                run_id=run_id,
            )
        
        # Calculate means
        hallucinations = [r.get("hallucination", 0.0) or 0.0 for r in attack_results]
        toxicities = [r.get("toxicity", 0.0) or 0.0 for r in attack_results]
        biases = [r.get("bias", 0.0) or 0.0 for r in attack_results]
        confidences = [r.get("confidence", 0.0) or 0.0 for r in attack_results]
        robustnesses = [r.get("robustness", 0.0) or 0.0 for r in attack_results if r.get("robustness") is not None]
        
        mean_h = sum(hallucinations) / len(hallucinations) if hallucinations else 0.0
        mean_t = sum(toxicities) / len(toxicities) if toxicities else 0.0
        mean_b = sum(biases) / len(biases) if biases else 0.0
        mean_c = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Calculate robustness under this attack using the formula
        # R_a = w_1(1-H_a) + w_2(1-T_a) + w_3(1-B_a) + w_4 * C_a
        w1, w2, w3, w4 = 0.25, 0.25, 0.25, 0.25
        robustness_a = w1 * (1 - mean_h) + w2 * (1 - mean_t) + w3 * (1 - mean_b) + w4 * mean_c
        
        # Calculate vulnerability index
        # If baseline available: VI_a = (R_base - R_adv) / R_base
        # Otherwise: VI_a = 1 - R_a
        # Ensure vulnerability_index is always >= 0
        if baseline_robustness is not None and baseline_robustness > 0:
            vulnerability_index = max(0.0, (baseline_robustness - robustness_a) / baseline_robustness)
        else:
            vulnerability_index = max(0.0, 1.0 - robustness_a)
        
        # Confidence collapse is 1 - mean_confidence
        confidence_collapse = 1.0 - mean_c
        
        return cls(
            attack_type=attack_type,
            sample_count=len(attack_results),
            mean_hallucination=mean_h,
            mean_toxicity=mean_t,
            mean_bias=mean_b,
            mean_confidence=mean_c,
            robustness=robustness_a,
            vulnerability_index=vulnerability_index,
            confidence_collapse=confidence_collapse,
            run_id=run_id,
        )

    def to_table_row(self) -> List[Any]:
        """
        Convert to table row for display.
        
        Returns:
            List of values for table row
        """
        return [
            self.attack_type,
            self.sample_count,
            f"{self.mean_hallucination:.3f}",
            f"{self.mean_toxicity:.3f}",
            f"{self.mean_bias:.3f}",
            f"{self.mean_confidence:.3f}",
            f"{self.robustness:.3f}",
            f"{self.vulnerability_index:.3f}",
        ]


class AttackBreakdownList(BaseModel):
    """
    Container for multiple attack breakdowns.
    """

    breakdowns: List[AttackBreakdown] = Field(
        description="List of attack breakdowns",
    )
    run_id: Optional[str] = Field(
        default=None,
        description="Evaluation run ID",
    )
    baseline_robustness: Optional[float] = Field(
        default=None,
        description="Baseline robustness score (if available)",
    )

    @classmethod
    def from_results(
        cls,
        results: List[Dict[str, Any]],
        run_id: Optional[str] = None,
    ) -> "AttackBreakdownList":
        """
        Create AttackBreakdownList from evaluation results.
        
        Args:
            results: List of evaluation result dictionaries
            run_id: Optional run ID
            
        Returns:
            AttackBreakdownList instance
        """
        # Get unique attack types
        attack_types = set()
        for result in results:
            attack_type = result.get("attack_type") or "none"
            attack_types.add(attack_type)
        
        # Calculate baseline robustness (from "none" attack type or overall)
        baseline_robustness = None
        none_results = [r for r in results if (r.get("attack_type") or "none") == "none"]
        if none_results:
            # Calculate from none attack results
            conf = [r.get("confidence", 0.0) or 0.0 for r in none_results]
            hal = [r.get("hallucination", 0.0) or 0.0 for r in none_results]
            tox = [r.get("toxicity", 0.0) or 0.0 for r in none_results]
            bias = [r.get("bias", 0.0) or 0.0 for r in none_results]
            
            if conf and hal and tox and bias:
                mean_c = sum(conf) / len(conf)
                mean_h = sum(hal) / len(hal)
                mean_t = sum(tox) / len(tox)
                mean_b = sum(bias) / len(bias)
                w1, w2, w3, w4 = 0.25, 0.25, 0.25, 0.25
                baseline_robustness = w1 * (1 - mean_h) + w2 * (1 - mean_t) + w3 * (1 - mean_b) + w4 * mean_c
        
        # Create breakdown for each attack type
        breakdowns = []
        for attack_type in sorted(attack_types):
            breakdown = AttackBreakdown.from_results(
                results=results,
                attack_type=attack_type,
                baseline_robustness=baseline_robustness,
                run_id=run_id,
            )
            breakdowns.append(breakdown)
        
        return cls(
            breakdowns=breakdowns,
            run_id=run_id,
            baseline_robustness=baseline_robustness,
        )


# =============================================================================
# Comparison Schemas
# =============================================================================


class DeltaRobustnessData(BaseModel):
    """
    Data schema for delta robustness comparison chart.
    
    Represents the change in robustness score between models or runs.
    """

    model_name: str = Field(
        description="Model name",
    )
    delta_robustness: float = Field(
        description="Delta robustness score (change from baseline)",
        ge=-1.0,
        le=1.0,
    )
    composite_score: float = Field(
        description="Absolute composite robustness score",
        ge=0.0,
        le=1.0,
    )
    rank: int = Field(
        description="Rank among compared models",
        ge=1,
    )


class ComparisonData(BaseModel):
    """
    Data schema for model comparison.
    
    Contains multiple models' metrics for side-by-side comparison.
    """

    models: List[str] = Field(
        description="List of model names",
    )
    hallucination: List[float] = Field(
        description="Mean hallucination per model",
    )
    toxicity: List[float] = Field(
        description="Mean toxicity per model",
    )
    bias: List[float] = Field(
        description="Mean bias per model",
    )
    confidence: List[float] = Field(
        description="Mean confidence per model",
    )
    composite_score: List[float] = Field(
        description="Composite robustness score per model",
    )
    sample_count: List[int] = Field(
        description="Sample count per model",
    )


# =============================================================================
# Metric Summary Schemas
# =============================================================================


class MetricSummary(BaseModel):
    """
    Statistical summary of a single metric.
    
    Displays mean, std, min, max, and sample count.
    """

    metric_name: str = Field(
        description="Name of the metric",
    )
    mean: float = Field(
        description="Mean value",
        ge=0.0,
        le=1.0,
    )
    std: float = Field(
        description="Standard deviation",
        ge=0.0,
        le=1.0,
    )
    min: float = Field(
        description="Minimum value",
        ge=0.0,
        le=1.0,
    )
    max: float = Field(
        description="Maximum value",
        ge=0.0,
        le=1.0,
    )
    count: int = Field(
        description="Number of samples",
        ge=0,
    )

    @classmethod
    def from_values(
        cls,
        metric_name: str,
        values: List[float],
    ) -> "MetricSummary":
        """
        Calculate summary statistics from a list of values.
        
        Args:
            metric_name: Name of the metric
            values: List of metric values
            
        Returns:
            MetricSummary instance
        """
        if not values:
            return cls(
                metric_name=metric_name,
                mean=0.0,
                std=0.0,
                min=0.0,
                max=0.0,
                count=0,
            )
        
        import math
        
        n = len(values)
        mean_val = sum(values) / n
        
        # Calculate std
        variance = sum((v - mean_val) ** 2 for v in values) / n
        std_val = math.sqrt(variance)
        
        return cls(
            metric_name=metric_name,
            mean=mean_val,
            std=std_val,
            min=min(values),
            max=max(values),
            count=n,
        )


# =============================================================================
# Run Summary Schemas
# =============================================================================


class RunMetadata(BaseModel):
    """
    Metadata for an evaluation run.
    
    Includes configuration, dataset version, and model version info.
    """

    run_id: str = Field(
        description="Unique run identifier",
    )
    timestamp: datetime = Field(
        description="Run timestamp",
    )
    model_name: str = Field(
        description="Name of the evaluated model",
    )
    model_version: str = Field(
        description="Model version string",
    )
    dataset_version: str = Field(
        description="Dataset version used",
    )
    config_hash: str = Field(
        description="SHA256 hash of run configuration",
    )
    status: str = Field(
        description="Run status (pending, running, completed, failed)",
    )


class RunSummary(BaseModel):
    """
    Summary of an evaluation run.
    
    Contains aggregated metrics and metadata.
    """

    metadata: RunMetadata = Field(
        description="Run metadata",
    )
    metric_summary: List[MetricSummary] = Field(
        description="Summary statistics for each metric",
    )
    composite_score: Optional[float] = Field(
        default=None,
        description="Overall composite robustness score",
        ge=0.0,
        le=1.0,
    )
    total_samples: int = Field(
        description="Total number of samples evaluated",
        ge=0,
    )
    attack_coverage: List[str] = Field(
        description="List of attack types covered in the run",
    )
    vulnerability_index: float = Field(
        description="Aggregated vulnerability score (0 = safe, 1 = vulnerable)",
        ge=0.0,
        le=1.0,
    )

    @classmethod
    def calculate_vulnerability_index(
        cls,
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
        # Average of the negative metrics (higher is worse)
        return (hallucination + toxicity + bias) / 3.0


# =============================================================================
# Export Schemas
# =============================================================================


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    CSV = "csv"


class ExportRequest(BaseModel):
    """Request schema for exporting reports."""

    run_id: str = Field(
        description="Run ID to export",
    )
    format: ExportFormat = Field(
        default=ExportFormat.JSON,
        description="Export format",
    )
    include_config: bool = Field(
        default=True,
        description="Include configuration in export",
    )
    include_raw_outputs: bool = Field(
        default=False,
        description="Include raw model outputs (privacy sensitive)",
    )


class ExportReport(BaseModel):
    """Complete report for export."""

    report_id: str = Field(
        description="Unique report identifier",
    )
    generated_at: datetime = Field(
        description="Report generation timestamp",
    )
    run_metadata: RunMetadata = Field(
        description="Evaluation run metadata",
    )
    aggregate_metrics: Dict[str, float] = Field(
        description="Aggregate metric values",
    )
    delta_metrics: Optional[Dict[str, float]] = Field(
        default=None,
        description="Delta from baseline (if applicable)",
    )
    weights: Dict[str, float] = Field(
        description="Scoring weights used",
    )
    dataset_version: str = Field(
        description="Dataset version",
    )
    model_version: str = Field(
        description="Model version",
    )
    config_hash: str = Field(
        description="Configuration hash for reproducibility",
    )


# =============================================================================
# Benchmark Comparison Schemas
# =============================================================================


class BenchmarkModelResult(BaseModel):
    """
    Data schema for a single model's results in a benchmark comparison.
    
    Contains baseline and adversarial robustness scores along with
    computed metrics (delta, RSI, VI).
    """

    model_name: str = Field(
        description="Model name",
    )
    baseline_robustness: float = Field(
        description="Baseline robustness score (R_base)",
        ge=0.0,
        le=1.0,
    )
    adversarial_robustness: float = Field(
        description="Adversarial robustness score (R_adv)",
        ge=0.0,
        le=1.0,
    )
    delta_robustness: float = Field(
        description="Delta robustness (R_base - R_adv)",
        ge=-1.0,
        le=1.0,
    )
    rsi: float = Field(
        description="Robustness Stability Index (R_adv / R_base)",
        ge=0.0,
        le=2.0,
    )
    vulnerability_index: float = Field(
        description="Vulnerability Index (Delta / R_base)",
        ge=0.0,
        le=2.0,
    )
    rank: int = Field(
        description="Rank among compared models (1 = best)",
        ge=1,
    )
    sample_count: int = Field(
        description="Number of samples evaluated",
        ge=0,
    )

    @classmethod
    def from_scores(
        cls,
        model_name: str,
        baseline_robustness: float,
        adversarial_robustness: float,
        sample_count: int = 0,
    ) -> "BenchmarkModelResult":
        """
        Create BenchmarkModelResult from baseline and adversarial scores.
        
        Args:
            model_name: Model name
            baseline_robustness: Baseline robustness score
            adversarial_robustness: Adversarial robustness score
            sample_count: Number of samples evaluated
            
        Returns:
            BenchmarkModelResult instance
        """
        # Calculate delta robustness
        delta = baseline_robustness - adversarial_robustness
        
        # Calculate RSI (Robustness Stability Index)
        # RSI = R_adv / R_base (closer to 1 = more stable)
        rsi = adversarial_robustness / baseline_robustness if baseline_robustness > 0 else 0.0
        
        # Calculate Vulnerability Index
        # VI = Delta / R_base (higher = more fragile)
        vi = delta / baseline_robustness if baseline_robustness > 0 else 0.0
        
        return cls(
            model_name=model_name,
            baseline_robustness=baseline_robustness,
            adversarial_robustness=adversarial_robustness,
            delta_robustness=delta,
            rsi=rsi,
            vulnerability_index=vi,
            rank=1,  # Will be set by ranking function
            sample_count=sample_count,
        )

    def to_table_row(self) -> List[Any]:
        """
        Convert to table row for display.
        
        Returns:
            List of values for table row
        """
        return [
            str(self.rank),
            self.model_name,
            f"{self.baseline_robustness:.4f}",
            f"{self.adversarial_robustness:.4f}",
            f"{self.delta_robustness:.4f}",
            f"{self.rsi:.4f}",
            f"{self.vulnerability_index:.4f}",
            str(self.sample_count),
        ]


class BenchmarkComparisonData(BaseModel):
    """
    Data schema for benchmark comparison across multiple models.
    
    Contains list of model results along with benchmark metadata.
    """

    benchmark_id: str = Field(
        description="Benchmark identifier",
    )
    benchmark_name: str = Field(
        description="Human-readable benchmark name",
    )
    dataset_version: str = Field(
        description="Dataset version used",
    )
    timestamp: datetime = Field(
        description="Benchmark execution timestamp",
    )
    model_results: List[BenchmarkModelResult] = Field(
        description="List of model results",
    )
    total_models: int = Field(
        description="Total number of models compared",
    )

    @classmethod
    def from_json(
        cls,
        benchmark_id: str,
        data: Dict[str, Any],
    ) -> "BenchmarkComparisonData":
        """
        Create BenchmarkComparisonData from JSON artifact.
        
        Args:
            benchmark_id: Benchmark identifier
            data: Dictionary from benchmark JSON file
            
        Returns:
            BenchmarkComparisonData instance
        """
        # Extract metadata
        metadata = data.get("metadata", {})
        models_data = data.get("models", [])
        
        # Create model results
        model_results = []
        for model_data in models_data:
            result = BenchmarkModelResult.from_scores(
                model_name=model_data.get("model_name", "unknown"),
                baseline_robustness=model_data.get("baseline_robustness", 0.0),
                adversarial_robustness=model_data.get("adversarial_robustness", 0.0),
                sample_count=model_data.get("sample_count", 0),
            )
            model_results.append(result)
        
        # Sort by adversarial robustness (descending) for ranking
        model_results.sort(
            key=lambda x: (x.adversarial_robustness, -x.vulnerability_index),
            reverse=True,
        )
        
        # Assign ranks
        for i, result in enumerate(model_results):
            result.rank = i + 1
        
        return cls(
            benchmark_id=benchmark_id,
            benchmark_name=metadata.get("name", f"Benchmark {benchmark_id}"),
            dataset_version=metadata.get("dataset_version", "unknown"),
            timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.utcnow().isoformat())),
            model_results=model_results,
            total_models=len(model_results),
        )

    def get_ranking_table_data(self) -> List[List[str]]:
        """
        Get ranking table data for display.
        
        Returns:
            List of table rows
        """
        return [result.to_table_row() for result in self.model_results]


class BenchmarkStats(BaseModel):
    """
    Statistical summary for a benchmark comparison.
    
    Contains aggregate statistics across all models.
    """

    benchmark_id: str = Field(
        description="Benchmark identifier",
    )
    mean_baseline: float = Field(
        description="Mean baseline robustness across models",
    )
    mean_adversarial: float = Field(
        description="Mean adversarial robustness across models",
    )
    mean_delta: float = Field(
        description="Mean delta robustness across models",
    )
    mean_rsi: float = Field(
        description="Mean RSI across models",
    )
    std_baseline: float = Field(
        description="Standard deviation of baseline robustness",
    )
    std_adversarial: float = Field(
        description="Standard deviation of adversarial robustness",
    )
    best_model: str = Field(
        description="Best performing model (highest R_adv)",
    )
    worst_model: str = Field(
        description="Worst performing model (lowest R_adv)",
    )
    most_vulnerable: str = Field(
        description="Most vulnerable model (highest VI)",
    )
    most_stable: str = Field(
        description="Most stable model (highest RSI)",
    )
    total_models: int = Field(
        description="Total number of models",
    )

    @classmethod
    def from_comparison_data(
        cls,
        benchmark_id: str,
        comparison: BenchmarkComparisonData,
    ) -> "BenchmarkStats":
        """
        Create BenchmarkStats from comparison data.
        
        Args:
            benchmark_id: Benchmark identifier
            comparison: BenchmarkComparisonData instance
            
        Returns:
            BenchmarkStats instance
        """
        if not comparison.model_results:
            return cls(
                benchmark_id=benchmark_id,
                mean_baseline=0.0,
                mean_adversarial=0.0,
                mean_delta=0.0,
                mean_rsi=0.0,
                std_baseline=0.0,
                std_adversarial=0.0,
                best_model="N/A",
                worst_model="N/A",
                most_vulnerable="N/A",
                most_stable="N/A",
                total_models=0,
            )
        
        import math
        
        baselines = [r.baseline_robustness for r in comparison.model_results]
        adversarials = [r.adversarial_robustness for r in comparison.model_results]
        deltas = [r.delta_robustness for r in comparison.model_results]
        rsis = [r.rsi for r in comparison.model_results]
        
        # Calculate means
        n = len(baselines)
        mean_baseline = sum(baselines) / n
        mean_adversarial = sum(adversarials) / n
        mean_delta = sum(deltas) / n
        mean_rsi = sum(rsis) / n
        
        # Calculate standard deviations
        var_baseline = sum((b - mean_baseline) ** 2 for b in baselines) / n
        var_adversarial = sum((a - mean_adversarial) ** 2 for a in adversarials) / n
        std_baseline = math.sqrt(var_baseline)
        std_adversarial = math.sqrt(var_adversarial)
        
        # Find best/worst/most vulnerable/most stable
        best_model = max(comparison.model_results, key=lambda x: x.adversarial_robustness).model_name
        worst_model = min(comparison.model_results, key=lambda x: x.adversarial_robustness).model_name
        most_vulnerable = max(comparison.model_results, key=lambda x: x.vulnerability_index).model_name
        most_stable = max(comparison.model_results, key=lambda x: x.rsi).model_name
        
        return cls(
            benchmark_id=benchmark_id,
            mean_baseline=mean_baseline,
            mean_adversarial=mean_adversarial,
            mean_delta=mean_delta,
            mean_rsi=mean_rsi,
            std_baseline=std_baseline,
            std_adversarial=std_adversarial,
            best_model=best_model,
            worst_model=worst_model,
            most_vulnerable=most_vulnerable,
            most_stable=most_stable,
            total_models=n,
        )


class BenchmarkInfo(BaseModel):
    """
    Information about a benchmark for listing.
    """

    benchmark_id: str = Field(
        description="Benchmark identifier",
    )
    name: str = Field(
        description="Human-readable name",
    )
    dataset_version: str = Field(
        description="Dataset version",
    )
    timestamp: datetime = Field(
        description="Creation timestamp",
    )
    model_count: int = Field(
        description="Number of models in benchmark",
    )
    total_samples: int = Field(
        description="Total samples evaluated",
    )

    @classmethod
    def from_json(
        cls,
        benchmark_id: str,
        data: Dict[str, Any],
    ) -> "BenchmarkInfo":
        """
        Create BenchmarkInfo from JSON artifact.
        
        Args:
            benchmark_id: Benchmark identifier
            data: Dictionary from benchmark JSON file
            
        Returns:
            BenchmarkInfo instance
        """
        metadata = data.get("metadata", {})
        models_data = data.get("models", [])
        
        total_samples = sum(m.get("sample_count", 0) for m in models_data)
        
        return cls(
            benchmark_id=benchmark_id,
            name=metadata.get("name", f"Benchmark {benchmark_id}"),
            dataset_version=metadata.get("dataset_version", "unknown"),
            timestamp=datetime.fromisoformat(metadata.get("timestamp", datetime.utcnow().isoformat())),
            model_count=len(models_data),
            total_samples=total_samples,
        )
