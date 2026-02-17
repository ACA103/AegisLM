"""
Dataset Schemas

Pydantic models for dataset validation and processing.
Supports three dataset categories:
1. Factual QA Datasets
2. Safety Challenge Datasets
3. Synthetic Adversarial Datasets
"""

import hashlib
import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class DatasetCategory(str, Enum):
    """Categories of datasets supported by AegisLM."""
    FACTUAL = "factual"
    SAFETY = "safety"
    SYNTHETIC = "synthetic"


class EvaluationMode(str, Enum):
    """Evaluation mode for the dataset."""
    FACTUAL = "factual"
    SAFETY = "safety"


class EvaluationConfig(BaseModel):
    """Evaluation configuration for a dataset."""
    hallucination_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    toxicity_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    bias_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    evaluation_mode: EvaluationMode = Field(default=EvaluationMode.FACTUAL)


class FactualQASample(BaseModel):
    """Schema for factual QA dataset samples."""
    sample_id: str = Field(description="Unique identifier for the sample")
    prompt: str = Field(description="Input prompt/question")
    ground_truth: str = Field(description="Expected correct answer")
    category: str = Field(default="factual", description="Dataset category")

    @field_validator("sample_id", mode="before")
    @classmethod
    def generate_sample_id(cls, v: Optional[str]) -> str:
        """Generate sample_id if not provided."""
        if v is None or v == "":
            return str(uuid.uuid4())
        return v


class SafetyChallengeSample(BaseModel):
    """Schema for safety challenge dataset samples."""
    sample_id: str = Field(description="Unique identifier for the sample")
    prompt: str = Field(description="Input prompt (potentially harmful)")
    category: str = Field(default="safety", description="Dataset category")
    ground_truth: Optional[str] = Field(default=None, description="Optional ground truth")

    @field_validator("sample_id", mode="before")
    @classmethod
    def generate_sample_id(cls, v: Optional[str]) -> str:
        """Generate sample_id if not provided."""
        if v is None or v == "":
            return str(uuid.uuid4())
        return v


class MutationTrace(BaseModel):
    """Schema for mutation trace in synthetic datasets."""
    strategy: str = Field(description="Mutation strategy used")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    diversity_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class SyntheticAdversarialSample(BaseModel):
    """Schema for synthetic adversarial dataset samples."""
    sample_id: str = Field(description="Unique identifier for the sample")
    base_prompt: str = Field(description="Original base prompt")
    mutated_prompt: str = Field(description="Mutated adversarial prompt")
    mutation_trace: List[MutationTrace] = Field(
        default_factory=list,
        description="Trace of mutations applied"
    )
    category: str = Field(default="synthetic", description="Dataset category")

    @field_validator("sample_id", mode="before")
    @classmethod
    def generate_sample_id(cls, v: Optional[str]) -> str:
        """Generate sample_id if not provided."""
        if v is None or v == "":
            return str(uuid.uuid4())
        return v


class DatasetManifest(BaseModel):
    """Manifest for a processed dataset version."""
    dataset_name: str = Field(description="Name of the dataset")
    version: str = Field(description="Version string (e.g., v1.0)")
    source: str = Field(default="official", description="Source of the dataset")
    num_samples: int = Field(ge=0, description="Number of samples in the dataset")
    preprocessing_steps: List[str] = Field(
        default_factory=list,
        description="List of preprocessing steps applied"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    checksum: str = Field(description="SHA256 checksum of the dataset")
    evaluation_config: Optional[EvaluationConfig] = Field(
        default=None,
        description="Evaluation configuration"
    )
    categories: List[str] = Field(
        default_factory=list,
        description="Categories present in the dataset"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class DatasetRegistryEntry(BaseModel):
    """Entry in the dataset registry."""
    latest_version: str = Field(description="Latest available version")
    available_versions: List[str] = Field(
        default_factory=list,
        description="All available versions"
    )


class DatasetRegistry(BaseModel):
    """Registry of all available datasets."""
    datasets: Dict[str, DatasetRegistryEntry] = Field(
        default_factory=dict,
        description="Registry of datasets by name"
    )

    def add_dataset(
        self,
        dataset_name: str,
        version: str,
    ) -> None:
        """Add or update a dataset in the registry."""
        if dataset_name not in self.datasets:
            self.datasets[dataset_name] = DatasetRegistryEntry(
                latest_version=version,
                available_versions=[version],
            )
        else:
            entry = self.datasets[dataset_name]
            if version not in entry.available_versions:
                entry.available_versions.append(version)
            if self._version_compare(version, entry.latest_version) > 0:
                entry.latest_version = version

    def get_latest_version(self, dataset_name: str) -> Optional[str]:
        """Get the latest version of a dataset."""
        if dataset_name in self.datasets:
            return self.datasets[dataset_name].latest_version
        return None

    def get_available_versions(self, dataset_name: str) -> List[str]:
        """Get all available versions of a dataset."""
        if dataset_name in self.datasets:
            return self.datasets[dataset_name].available_versions
        return []

    @staticmethod
    def _version_compare(v1: str, v2: str) -> int:
        """Compare two version strings. Returns 1 if v1 > v2, -1 if v1 < v2, 0 if equal."""
        parts1 = v1.lstrip("v").split(".")
        parts2 = v2.lstrip("v").split(".")
        
        for p1, p2 in zip(parts1, parts2):
            if int(p1) > int(p2):
                return 1
            elif int(p1) < int(p2):
                return -1
        
        if len(parts1) > len(parts2):
            return 1
        elif len(parts1) < len(parts2):
            return -1
        
        return 0


class SamplingConfig(BaseModel):
    """Configuration for dataset sampling."""
    method: str = Field(
        default="full",
        description="Sampling method: full, stratified, or category_based"
    )
    sample_size: Optional[int] = Field(
        default=None,
        ge=1,
        description="Number of samples to sample (for stratified/category_based)"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Categories to sample from (for category_based)"
    )
    seed: Optional[int] = Field(
        default=None,
        description="Random seed for reproducibility"
    )

    def generate_seed(self, run_id: str, dataset_version: str) -> int:
        """
        Generate a deterministic seed based on run_id and dataset_version.
        
        This ensures reproducibility across runs.
        """
        if self.seed is not None:
            return self.seed
        
        # Generate deterministic seed from run_id and dataset_version
        seed_string = f"{run_id}_{dataset_version}"
        hash_object = hashlib.sha256(seed_string.encode())
        return int(hash_object.hexdigest()[:8], 16)


class DatasetMetadata(BaseModel):
    """Metadata for a loaded dataset."""
    dataset_name: str
    version: str
    num_samples: int
    categories: List[str]
    checksum: str
    sampling_method: str
    sample_size: Optional[int] = None
    evaluation_config: Optional[EvaluationConfig] = None


def compute_checksum(data: List[Dict[str, Any]]) -> str:
    """
    Compute SHA256 checksum over dataset content.
    
    Uses sorted JSON serialization for deterministic results.
    
    Args:
        data: List of sample dictionaries
        
    Returns:
        SHA256 checksum string
    """
    # Sort keys recursively for deterministic serialization
    def sort_dict(obj):
        if isinstance(obj, dict):
            return {k: sort_dict(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            return [sort_dict(item) for item in obj]
        return obj
    
    sorted_data = [sort_dict(item) for item in data]
    serialized = json.dumps(sorted_data, sort_keys=True, ensure_ascii=False)
    
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
