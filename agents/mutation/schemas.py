"""
Mutation Schemas

Typed contracts for mutation engine requests and responses.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MutationRequest(BaseModel):
    """Request schema for prompt mutation."""
    
    run_id: UUID = Field(description="Unique identifier for the evaluation run")
    sample_id: str = Field(description="Identifier for the dataset sample")
    base_prompt: str = Field(description="Original prompt to be mutated")
    attack_type: str = Field(
        description="Type of attack being mutated",
        examples=["jailbreak", "injection", "bias_trigger", "context_poison", "role_confusion", "chaining"]
    )
    mutation_depth: int = Field(
        default=1,
        description="Number of mutation iterations (1-3)",
        ge=1,
        le=3
    )
    random_seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility (auto-computed if not provided)"
    )


class MutationResponse(BaseModel):
    """Response schema for prompt mutation."""
    
    mutated_prompt: str = Field(description="The mutated adversarial prompt")
    mutation_trace: List[str] = Field(
        description="List of mutation strategies applied in order",
        examples=[["synonym_replacement", "context_obfuscation", "paraphrase"]]
    )
    diversity_score: float = Field(
        description="Diversity score between base and mutated prompt",
        ge=0.0,
        le=1.0
    )
    cumulative_diversity: float = Field(
        description="Cumulative diversity across all mutation steps",
        ge=0.0,
        le=1.0
    )
    mutation_depth: int = Field(description="Actual depth of mutation applied")
    mutation_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the mutation"
    )
    run_id: UUID = Field(description="Run identifier for traceability")
    sample_id: str = Field(description="Sample identifier for traceability")


class MutationLog(BaseModel):
    """Schema for mutation execution logging."""
    
    run_id: UUID = Field(description="Unique identifier for the evaluation run")
    sample_id: str = Field(description="Identifier for the dataset sample")
    attack_type: str = Field(description="Type of attack being mutated")
    mutation_depth: int = Field(description="Depth of mutation applied")
    strategies_used: List[str] = Field(description="List of strategies applied")
    diversity_score: float = Field(
        description="Final diversity score between base and mutated prompt"
    )
    cumulative_diversity: float = Field(
        description="Cumulative diversity across all steps"
    )
    success: bool = Field(description="Whether mutation succeeded")
    error: Optional[str] = Field(
        default=None,
        description="Error message if mutation failed"
    )


class MutationStrategyConfig(BaseModel):
    """Configuration for a specific mutation strategy."""
    
    strategy_name: str = Field(description="Name of the mutation strategy")
    enabled: bool = Field(default=True, description="Whether strategy is enabled")
    probability: float = Field(
        default=0.5,
        description="Probability of applying this strategy",
        ge=0.0,
        le=1.0
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Strategy-specific parameters"
    )
