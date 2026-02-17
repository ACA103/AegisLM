"""
SQLAlchemy ORM Models

Defines database schema for AegisLM evaluation framework.
Tables: evaluation_runs, evaluation_results, model_versions, dataset_versions
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# =============================================================================
# Table 1: evaluation_runs
# =============================================================================

class EvaluationRun(Base):
    """
    Represents a single evaluation run.
    
    Tracks the overall lifecycle and results of evaluating a model
    against a specific dataset version.
    """

    __tablename__ = "evaluation_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the evaluation run"
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        doc="When the evaluation run was initiated"
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Name of the model being evaluated"
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Version identifier of the model"
    )

    dataset_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Version of the dataset used"
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        doc="Status: pending, running, completed, failed, cancelled"
    )

    config_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA256 hash of configuration for reproducibility"
    )

    composite_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Final composite robustness score (0-1)"
    )

    # Relationships
    results: Mapped[list["EvaluationResult"]] = relationship(
        "EvaluationResult",
        back_populates="run",
        cascade="all, delete-orphan",
        doc="Individual evaluation results for each sample"
    )

    def __repr__(self) -> str:
        return f"<EvaluationRun(id={self.id}, model={self.model_name}, status={self.status})>"


# =============================================================================
# Table 2: evaluation_results
# =============================================================================

class EvaluationResult(Base):
    """
    Individual evaluation result for a single sample.
    
    Contains scores for each metric (hallucination, toxicity, bias, confidence)
    and the raw model output.
    """

    __tablename__ = "evaluation_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier for the result"
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("evaluation_runs.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to parent evaluation run"
    )

    sample_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Identifier of the sample from the dataset"
    )

    attack_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Type of attack applied (if any)"
    )

    mutation_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Type of mutation applied (if any)"
    )

    # Scoring metrics (all in [0, 1] range)
    hallucination: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Hallucination score (0 = no hallucination, 1 = full hallucination)"
    )

    toxicity: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Toxicity score (0 = non-toxic, 1 = toxic)"
    )

    bias: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Bias score (0 = unbiased, 1 = biased)"
    )

    confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Model confidence score (0 = low, 1 = high)"
    )

    # Computed robustness score
    robustness: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Computed robustness score for this sample"
    )

    # Raw outputs
    raw_output: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Raw model output text"
    )

    processed_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Prompt after attack/mutation processing"
    )

    # Metadata
    result_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional result metadata"
    )

    processing_time_ms: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="Time taken to process this sample in milliseconds"
    )

    # Relationships
    run: Mapped["EvaluationRun"] = relationship(
        "EvaluationRun",
        back_populates="results",
        doc="Parent evaluation run"
    )

    def __repr__(self) -> str:
        return f"<EvaluationResult(id={self.id}, sample={self.sample_id})>"


# =============================================================================
# Table 3: model_versions
# =============================================================================

class ModelVersion(Base):
    """
    Tracks registered model versions.
    
    Stores metadata about models that have been registered
    for evaluation in the system.
    """

    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier"
    )

    model_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Model name (e.g., meta-llama/Llama-2-7b-hf)"
    )

    model_version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Version string (e.g., v1.0, latest)"
    )

    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Model parameters (num_params, vocab_size, etc.)"
    )

    checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="SHA256 checksum of model weights"
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        doc="When this model version was registered"
    )

    last_used: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        doc="When this model was last used in evaluation"
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether this model version is available for evaluation"
    )

    def __repr__(self) -> str:
        return f"<ModelVersion(name={self.model_name}, version={self.model_version})>"


# =============================================================================
# Table 4: dataset_versions
# =============================================================================

class DatasetVersion(Base):
    """
    Tracks registered dataset versions.
    
    Stores metadata about datasets that have been registered
    for evaluation in the system.
    """

    __tablename__ = "dataset_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid.uuid4,
        doc="Unique identifier"
    )

    dataset_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        doc="Dataset name (e.g., aegislm-harmful-queries)"
    )

    version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Version string (e.g., v1.0)"
    )

    checksum: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        doc="SHA256 checksum of dataset file"
    )

    dataset_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="Additional dataset metadata (num_samples, categories, etc.)"
    )

    registered_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        doc="When this dataset version was registered"
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        doc="Whether this dataset version is available for evaluation"
    )

    def __repr__(self) -> str:
        return f"<DatasetVersion(name={self.dataset_name}, version={self.version})>"


# =============================================================================
# Helper functions
# =============================================================================

async def create_tables():
    """Create all tables in the database."""
    from backend.db.session import create_database_engine
    
    engine = create_database_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
