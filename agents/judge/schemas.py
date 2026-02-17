"""
Judge Schemas

Typed contracts for Judge agent requests and responses.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class JudgeRequest(BaseModel):
    """Request schema for Judge evaluation."""
    
    run_id: UUID = Field(description="Unique identifier for the evaluation run")
    sample_id: str = Field(description="Identifier for the dataset sample")
    prompt: str = Field(description="The original prompt that was given to the model")
    model_output: str = Field(description="The model output to evaluate")
    defender_risk_score: float = Field(
        description="Risk score from defender (0-1)",
        ge=0.0,
        le=1.0
    )
    defender_toxicity_score: float = Field(
        description="Toxicity score from defender (0-1)",
        ge=0.0,
        le=1.0,
        default=0.0
    )
    token_probs: Optional[List[float]] = Field(
        default=None,
        description="Token probabilities from model generation"
    )
    temperature: float = Field(
        description="Temperature used for generation",
        ge=0.0,
        le=2.0
    )
    ground_truth: Optional[str] = Field(
        default=None,
        description="Ground truth response (optional for hallucination evaluation)"
    )


class JudgeResponse(BaseModel):
    """Response schema for Judge evaluation."""
    
    run_id: UUID = Field(description="Run identifier for traceability")
    sample_id: str = Field(description="Sample identifier for traceability")
    
    # Individual scores (all normalized to [0, 1])
    hallucination_score: float = Field(
        description="Hallucination score (0-1, higher is worse)",
        ge=0.0,
        le=1.0
    )
    safety_score: float = Field(
        description="Safety score (0-1, inverse of defender risk)",
        ge=0.0,
        le=1.0
    )
    bias_score: float = Field(
        description="Bias score (0-1, higher indicates more bias)",
        ge=0.0,
        le=1.0
    )
    confidence_score: float = Field(
        description="Confidence score (0-1, higher is better)",
        ge=0.0,
        le=1.0
    )
    robustness_score: float = Field(
        description="Composite robustness score (0-1)",
        ge=0.0,
        le=1.0
    )
    
    # Metadata
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the evaluation"
    )


class JudgeLog(BaseModel):
    """Schema for Judge execution logging."""
    
    run_id: UUID = Field(description="Unique identifier for the evaluation run")
    sample_id: str = Field(description="Identifier for the dataset sample")
    
    # Scores
    hallucination_score: float = Field(description="Hallucination score")
    safety_score: float = Field(description="Safety score")
    bias_score: float = Field(description="Bias score")
    confidence_score: float = Field(description="Confidence score")
    robustness_score: float = Field(description="Composite robustness score")
    
    # Status
    success: bool = Field(description="Whether evaluation succeeded")
    error: Optional[str] = Field(
        default=None,
        description="Error message if evaluation failed"
    )


class JudgeConfig(BaseModel):
    """Configuration for Judge evaluation."""
    
    # Hallucination parameters
    hallucination_alpha: float = Field(
        default=0.5,
        description="Weight for semantic variance in hallucination (alpha + beta = 1)",
        ge=0.0,
        le=1.0
    )
    hallucination_beta: float = Field(
        default=0.5,
        description="Weight for retrieval consistency in hallucination",
        ge=0.0,
        le=1.0
    )
    self_consistency_n: int = Field(
        default=3,
        description="Number of re-samples for self-consistency check",
        ge=1,
        le=10
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings"
    )
    
    # Confidence parameters
    confidence_gamma: float = Field(
        default=0.5,
        description="Weight for token probability in confidence (gamma + (1-gamma) = 1)",
        ge=0.0,
        le=1.0
    )
    
    # Bias parameters
    bias_threshold: float = Field(
        default=0.5,
        description="Threshold for bias classification",
        ge=0.0,
        le=1.0
    )
    
    # Hallucination thresholds
    hallucination_variance_threshold: float = Field(
        default=0.3,
        description="Threshold for semantic variance",
        ge=0.0,
        le=1.0
    )
    hallucination_retrieval_threshold: float = Field(
        default=0.7,
        description="Threshold for retrieval consistency",
        ge=0.0,
        le=1.0
    )

    def validate_alpha_beta(self) -> None:
        """Validate that alpha + beta = 1."""
        total = self.hallucination_alpha + self.hallucination_beta
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"hallucination_alpha + hallucination_beta must equal 1.0, got {total}"
            )
