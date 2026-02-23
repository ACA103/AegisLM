"""
Adaptive Learning Schemas

Data models for the Adaptive Adversarial Learning Layer.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AdaptiveMode(str, Enum):
    """Adaptive evaluation modes."""
    DISABLED = "disabled"
    STANDARD = "standard"  # Basic vulnerability-guided selection
    AGGRESSIVE = "aggressive"  # Maximize stress testing
    CONSERVATIVE = "conservative"  # Balanced exploration


class VulnerabilityWeights(BaseModel):
    """Weights for vulnerability score calculation."""
    
    hallucination_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for hallucination in vulnerability",
    )
    toxicity_weight: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Weight for toxicity in vulnerability",
    )
    bias_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for bias in vulnerability",
    )
    confidence_weight: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Weight for (1 - confidence) in vulnerability",
    )
    
    @field_validator("hallucination_weight", "toxicity_weight", "bias_weight", "confidence_weight")
    @classmethod
    def validate_weight_range(cls, v: float) -> float:
        """Validate weight is in [0, 1] range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Weight must be in [0, 1], got {v}")
        return v
    
    def validate_sum(self) -> None:
        """Validate that weights sum to approximately 1.0."""
        total = (
            self.hallucination_weight
            + self.toxicity_weight
            + self.bias_weight
            + self.confidence_weight
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Vulnerability weights must sum to 1.0, got {total}")


class AttackVulnerability(BaseModel):
    """Vulnerability score for a specific attack class."""
    
    attack_type: str = Field(
        description="Type of attack (e.g., jailbreak, injection)",
    )
    vulnerability_score: float = Field(
        description="Computed vulnerability score [0, 1]",
        ge=0.0,
        le=1.0,
    )
    hallucination_impact: float = Field(
        description="Hallucination increase from this attack class",
        ge=0.0,
        le=1.0,
    )
    toxicity_impact: float = Field(
        description="Toxicity increase from this attack class",
        ge=0.0,
        le=1.0,
    )
    bias_impact: float = Field(
        description="Bias increase from this attack class",
        ge=0.0,
        le=1.0,
    )
    confidence_impact: float = Field(
        description="Confidence decrease from this attack class",
        ge=0.0,
        le=1.0,
    )
    sample_count: int = Field(
        description="Number of samples used to compute this vulnerability",
        ge=0,
    )
    last_updated: datetime = Field(
        description="Timestamp of last update",
    )
    
    @field_validator("hallucination_impact", "toxicity_impact", "bias_impact", "confidence_impact")
    @classmethod
    def validate_impact_range(cls, v: float) -> float:
        """Validate impact is in [0, 1] range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(f"Impact must be in [0, 1], got {v}")
        return v


class AdaptiveConfig(BaseModel):
    """Configuration for adaptive learning."""
    
    enabled: bool = Field(
        default=False,
        description="Enable adaptive adversarial mode",
    )
    mode: AdaptiveMode = Field(
        default=AdaptiveMode.STANDARD,
        description="Adaptive evaluation mode",
    )
    vulnerability_weights: VulnerabilityWeights = Field(
        default_factory=VulnerabilityWeights,
        description="Weights for vulnerability calculation",
    )
    entropy_regularization: float = Field(
        default=0.1,
        ge=0.0,
        le=0.5,
        description="Epsilon for entropy regularization to maintain diversity",
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum adaptive iterations",
    )
    compute_budget_minutes: int = Field(
        default=60,
        ge=1,
        le=480,
        description="Maximum compute budget in minutes",
    )
    base_mutation_depth: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Base mutation depth",
    )
    max_mutation_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum mutation depth for high vulnerability attacks",
    )
    evolution_smoothing: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Smoothing factor for exponential moving average (lambda)",
    )
    min_samples_for_adaptation: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Minimum samples before adapting",
    )
    convergence_threshold: float = Field(
        default=0.01,
        ge=0.0,
        le=0.5,
        description="Convergence threshold for adaptive loop",
    )
    
    def validate_config(self) -> None:
        """Validate configuration."""
        self.vulnerability_weights.validate_sum()
        
        if self.base_mutation_depth > self.max_mutation_depth:
            raise ValueError(
                f"Base mutation depth ({self.base_mutation_depth}) must be <= "
                f"max mutation depth ({self.max_mutation_depth})"
            )


class AdaptiveSelectionProbabilities(BaseModel):
    """Attack selection probabilities based on vulnerability."""
    
    iteration: int = Field(
        description="Current adaptive iteration",
        ge=0,
    )
    probabilities: Dict[str, float] = Field(
        description="Probability for each attack type",
    )
    mutation_depths: Dict[str, int] = Field(
        description="Mutation depth for each attack type",
    )
    entropy: float = Field(
        description="Entropy of probability distribution",
        ge=0.0,
    )
    timestamp: datetime = Field(
        description="When these probabilities were computed",
    )


class AttackHistoryEntry(BaseModel):
    """Entry in attack performance history."""
    
    attack_type: str = Field(description="Type of attack")
    baseline_hallucination: float = Field(
        description="Baseline hallucination score",
        ge=0.0,
        le=1.0,
    )
    adversarial_hallucination: float = Field(
        description="Adversarial hallucination score",
        ge=0.0,
        le=1.0,
    )
    hallucination_delta: float = Field(
        description="Increase in hallucination (adversarial - baseline)",
    )
    baseline_toxicity: float = Field(
        description="Baseline toxicity score",
        ge=0.0,
        le=1.0,
    )
    adversarial_toxicity: float = Field(
        description="Adversarial toxicity score",
        ge=0.0,
        le=1.0,
    )
    toxicity_delta: float = Field(
        description="Increase in toxicity (adversarial - baseline)",
    )
    baseline_bias: float = Field(
        description="Baseline bias score",
        ge=0.0,
        le=1.0,
    )
    adversarial_bias: float = Field(
        description="Adversarial bias score",
        ge=0.0,
        le=1.0,
    )
    bias_delta: float = Field(
        description="Increase in bias (adversarial - baseline)",
    )
    baseline_confidence: float = Field(
        description="Baseline confidence score",
        ge=0.0,
        le=1.0,
    )
    adversarial_confidence: float = Field(
        description="Adversarial confidence score",
        ge=0.0,
        le=1.0,
    )
    confidence_delta: float = Field(
        description="Decrease in confidence (baseline - adversarial)",
    )
    baseline_robustness: float = Field(
        description="Baseline robustness score",
        ge=0.0,
        le=1.0,
    )
    adversarial_robustness: float = Field(
        description="Adversarial robustness score",
        ge=0.0,
        le=1.0,
    )
    robustness_delta: float = Field(
        description="Robustness drop (baseline - adversarial)",
    )
    model_name: str = Field(description="Model evaluated")
    dataset_name: str = Field(description="Dataset used")
    timestamp: datetime = Field(description="When this evaluation occurred")


class AdaptiveIterationResult(BaseModel):
    """Result from a single adaptive iteration."""
    
    iteration: int = Field(description="Iteration number")
    attack_probabilities: Dict[str, float] = Field(
        description="Attack selection probabilities used",
    )
    vulnerabilities: Dict[str, float] = Field(
        description="Computed vulnerability scores",
    )
    worst_case_robustness: float = Field(
        description="Worst-case robustness observed",
        ge=0.0,
        le=1.0,
    )
    mean_robustness: float = Field(
        description="Mean robustness across all attacks",
        ge=0.0,
        le=1.0,
    )
    convergence_delta: float = Field(
        description="Change in worst-case robustness from previous iteration",
    )
    compute_time_seconds: float = Field(
        description="Time taken for this iteration",
    )
    samples_evaluated: int = Field(
        description="Total samples evaluated in this iteration",
    )


class AdaptiveEvaluationResult(BaseModel):
    """Complete result from adaptive evaluation."""
    
    config: AdaptiveConfig = Field(description="Adaptive configuration used")
    total_iterations: int = Field(
        description="Number of adaptive iterations completed",
    )
    converged: bool = Field(
        description="Whether adaptive loop converged",
    )
    final_worst_case_robustness: float = Field(
        description="Final worst-case robustness",
        ge=0.0,
        le=1.0,
    )
    initial_worst_case_robustness: float = Field(
        description="Initial worst-case robustness",
        ge=0.0,
        le=1.0,
    )
    robustness_improvement: float = Field(
        description="Improvement in worst-case robustness",
    )
    iteration_results: List[AdaptiveIterationResult] = Field(
        description="Results from each iteration",
    )
    final_vulnerabilities: Dict[str, float] = Field(
        description="Final vulnerability scores",
    )
    total_compute_time_seconds: float = Field(
        description="Total compute time",
    )
    total_samples_evaluated: int = Field(
        description="Total samples evaluated",
    )
    config_hash: str = Field(
        description="Hash of adaptive configuration for reproducibility",
    )
    started_at: datetime = Field(description="When evaluation started")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When evaluation completed",
    )


__all__ = [
    "AdaptiveMode",
    "VulnerabilityWeights",
    "AttackVulnerability",
    "AdaptiveConfig",
    "AdaptiveSelectionProbabilities",
    "AttackHistoryEntry",
    "AdaptiveIterationResult",
    "AdaptiveEvaluationResult",
]
