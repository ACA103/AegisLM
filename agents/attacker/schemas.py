"""
Attack Schemas

Typed contracts for attacker agent requests and responses.
"""

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AttackRequest(BaseModel):
    """Request schema for attack generation."""
    
    run_id: UUID = Field(description="Unique identifier for the evaluation run")
    sample_id: str = Field(description="Identifier for the dataset sample")
    base_prompt: str = Field(description="Original prompt to be mutated")
    attack_type: str = Field(
        description="Type of attack to generate",
        examples=["jailbreak", "injection", "bias_trigger", "context_poison", "role_confusion", "chaining"]
    )
    temperature: float = Field(
        description="Temperature for generation",
        ge=0.0,
        le=2.0
    )
    chain_depth: int = Field(
        default=1,
        description="Depth of attack chaining",
        ge=1,
        le=10
    )
    protected_attributes: Optional[list[str]] = Field(
        default=None,
        description="List of protected attributes for bias attacks"
    )


class AttackResponse(BaseModel):
    """Response schema for attack generation."""
    
    mutated_prompt: str = Field(description="The adversarial mutated prompt")
    attack_type: str = Field(description="Type of attack that was applied")
    temperature: float = Field(description="Temperature used for generation")
    chain_depth: int = Field(description="Actual chain depth applied")
    attack_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the attack"
    )
    diversity_score: Optional[float] = Field(
        default=None,
        description="Diversity score between base and mutated prompt",
        ge=0.0,
        le=1.0
    )
    run_id: UUID = Field(description="Run identifier for traceability")
    sample_id: str = Field(description="Sample identifier for traceability")


class AttackLog(BaseModel):
    """Schema for attack execution logging."""
    
    run_id: UUID = Field(description="Unique identifier for the evaluation run")
    sample_id: str = Field(description="Identifier for the dataset sample")
    attack_type: str = Field(description="Type of attack applied")
    chain_depth: int = Field(description="Depth of attack chaining")
    temperature: float = Field(description="Temperature used for generation")
    diversity_score: Optional[float] = Field(
        default=None,
        description="Diversity score between base and mutated prompt"
    )
    success: bool = Field(description="Whether attack generation succeeded")
    error: Optional[str] = Field(
        default=None,
        description="Error message if attack generation failed"
    )
