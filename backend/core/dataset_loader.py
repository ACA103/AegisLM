"""
Dataset Loader Module

Handles dataset loading, preprocessing, versioning, and sampling.
Implements the Dataset Ingestion & Versioning Pipeline for AegisLM.

Key Features:
- Deterministic preprocessing
- SHA256 checksum verification
- Dataset versioning with manifest
- Multiple sampling strategies
- Integration with orchestrator
"""

import hashlib
import json
import random
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Union

from backend.core.dataset_schemas import (
    DatasetCategory,
    DatasetManifest,
    DatasetMetadata,
    DatasetRegistry,
    EvaluationConfig,
    EvaluationMode,
    FactualQASample,
    SamplingConfig,
    SafetyChallengeSample,
    SyntheticAdversarialSample,
    compute_checksum,
)
from backend.logging.logger import get_logger


# Default paths
DEFAULT_RAW_PATH = Path("datasets/raw")
DEFAULT_PROCESSED_PATH = Path("datasets/processed")
DEFAULT_REGISTRY_PATH = Path("datasets/registry")
DEFAULT_DATASET_REGISTRY_FILE = "dataset_registry.json"


class DatasetLoader:
    """
    Main dataset loader class.
    
    Handles loading, preprocessing, versioning, and sampling of datasets.
    Implements deterministic preprocessing and checksum verification.
    """

    def __init__(
        self,
        raw_path: Optional[Path] = None,
        processed_path: Optional[Path] = None,
        registry_path: Optional[Path] = None,
    ):
        """
        Initialize the dataset loader.
        
        Args:
            raw_path: Path to raw datasets directory
            processed_path: Path to processed datasets directory
            registry_path: Path to dataset registry directory
        """
        self.raw_path = raw_path or DEFAULT_RAW_PATH
        self.processed_path = processed_path or DEFAULT_PROCESSED_PATH
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.logger = get_logger(__name__)
        
        # Ensure directories exist
        self.raw_path.mkdir(parents=True, exist_ok=True)
        self.processed_path.mkdir(parents=True, exist_ok=True)
        self.registry_path.mkdir(parents=True, exist_ok=True)
        
        # Load or initialize registry
        self._registry = self._load_registry()

    def _load_registry(self) -> DatasetRegistry:
        """Load the dataset registry from disk."""
        registry_file = self.registry_path / DEFAULT_DATASET_REGISTRY_FILE
        
        if registry_file.exists():
            with open(registry_file, "r") as f:
                data = json.load(f)
                return DatasetRegistry(datasets=data.get("datasets", {}))
        
        return DatasetRegistry()

    def _save_registry(self) -> None:
        """Save the dataset registry to disk."""
        registry_file = self.registry_path / DEFAULT_DATASET_REGISTRY_FILE
        
        with open(registry_file, "w") as f:
            json.dump(
                {"datasets": self._registry.datasets},
                f,
                indent=2,
            )

    def load_raw_dataset(
        self,
        name: str,
        category: Optional[DatasetCategory] = None,
    ) -> List[Dict[str, Any]]:
        """
        Load a raw dataset by name.
        
        Args:
            name: Name of the dataset (e.g., 'truthfulqa', 'advbench')
            category: Optional category filter
            
        Returns:
            List of raw sample dictionaries
        """
        dataset_path = self.raw_path / name / "data.json"
        
        if not dataset_path.exists():
            raise FileNotFoundError(f"Raw dataset not found: {dataset_path}")
        
        with open(dataset_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self.logger.info(
            "Loaded raw dataset",
            dataset_name=name,
            num_samples=len(data),
        )
        
        return data

    def preprocess_dataset(
        self,
        raw_data: List[Dict[str, Any]],
        category: DatasetCategory,
    ) -> List[Dict[str, Any]]:
        """
        Preprocess dataset with deterministic rules.
        
        Rules applied:
        - Strip whitespace
        - Normalize encoding
        - Ensure unique sample IDs
        - Remove duplicates
        - Standardize schema fields
        
        Args:
            raw_data: List of raw sample dictionaries
            category: Dataset category
            
        Returns:
            List of preprocessed sample dictionaries
        """
        preprocessing_steps = []
        processed_data = []
        seen_prompts = set()
        
        for sample in raw_data:
            # Strip whitespace from text fields
            if "prompt" in sample:
                sample["prompt"] = sample["prompt"].strip()
            if "ground_truth" in sample and sample["ground_truth"]:
                sample["ground_truth"] = sample["ground_truth"].strip()
            if "base_prompt" in sample:
                sample["base_prompt"] = sample["base_prompt"].strip()
            if "mutated_prompt" in sample:
                sample["mutated_prompt"] = sample["mutated_prompt"].strip()
            
            # Generate sample_id if not present
            if "sample_id" not in sample or not sample["sample_id"]:
                sample["sample_id"] = str(uuid.uuid4())
            
            # Normalize encoding (basic ASCII normalization)
            if "prompt" in sample:
                sample["prompt"] = sample["prompt"].encode("ascii", "ignore").decode("ascii")
            if "ground_truth" in sample and sample["ground_truth"]:
                sample["ground_truth"] = sample["ground_truth"].encode("ascii", "ignore").decode("ascii")
            
            # Remove duplicates based on prompt
            prompt_key = sample.get("prompt", sample.get("base_prompt", ""))
            if prompt_key not in seen_prompts:
                seen_prompts.add(prompt_key)
                
                # Add category if not present
                if "category" not in sample:
                    sample["category"] = category.value
                
                processed_data.append(sample)
        
        preprocessing_steps.extend([
            "whitespace cleanup",
            "encoding normalization",
            "unique sample ID generation",
            "duplicate removal",
            "schema field standardization",
        ])
        
        self.logger.info(
            "Preprocessed dataset",
            original_count=len(raw_data),
            processed_count=len(processed_data),
            steps=preprocessing_steps,
        )
        
        return processed_data

    def save_processed_dataset(
        self,
        name: str,
        version: str,
        processed_data: List[Dict[str, Any]],
        preprocessing_steps: List[str],
        evaluation_config: Optional[EvaluationConfig] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Save processed dataset with manifest.
        
        Args:
            name: Dataset name
            version: Version string
            processed_data: Preprocessed dataset
            preprocessing_steps: List of preprocessing steps applied
            evaluation_config: Optional evaluation configuration
            metadata: Optional additional metadata
            
        Returns:
            Path to the saved dataset
        """
        # Compute checksum
        checksum = compute_checksum(processed_data)
        
        # Determine categories
        categories = list(set(
            sample.get("category", "unknown") 
            for sample in processed_data
        ))
        
        # Create manifest
        manifest = DatasetManifest(
            dataset_name=name,
            version=version,
            source="official",
            num_samples=len(processed_data),
            preprocessing_steps=preprocessing_steps,
            created_at=datetime.utcnow(),
            checksum=checksum,
            evaluation_config=evaluation_config,
            categories=categories,
            metadata=metadata or {},
        )
        
        # Save version directory
        version_dir = self.processed_path / f"v{version.lstrip('v')}"
        version_dir.mkdir(parents=True, exist_ok=True)
        
        # Save data file
        data_file = version_dir / "data.json"
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(processed_data, f, indent=2, ensure_ascii=False)
        
        # Save manifest
        manifest_file = version_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(manifest.model_dump(), f, indent=2, default=str)
        
        # Update registry
        self._registry.add_dataset(name, version)
        self._save_registry()
        
        self.logger.info(
            "Saved processed dataset",
            dataset_name=name,
            version=version,
            num_samples=len(processed_data),
            checksum=checksum,
        )
        
        return version_dir

    def load_processed_dataset(
        self,
        name: str,
        version: Optional[str] = None,
        verify_checksum: bool = True,
    ) -> tuple[List[Dict[str, Any]], DatasetMetadata]:
        """
        Load a processed dataset with version and checksum verification.
        
        Args:
            name: Dataset name
            version: Specific version to load (None for latest)
            verify_checksum: Whether to verify checksum
            
        Returns:
            Tuple of (dataset samples, metadata)
        """
        # Get version
        if version is None:
            version = self._registry.get_latest_version(name)
            if version is None:
                raise ValueError(f"No version found for dataset: {name}")
        
        # Load manifest
        version_dir = self.processed_path / f"v{version.lstrip('v')}"
        manifest_file = version_dir / "manifest.json"
        
        if not manifest_file.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_file}")
        
        with open(manifest_file, "r") as f:
            manifest_data = json.load(f)
        
        manifest = DatasetManifest(**manifest_data)
        
        # Load data
        data_file = version_dir / "data.json"
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Verify checksum if requested
        if verify_checksum:
            computed_checksum = compute_checksum(data)
            if computed_checksum != manifest.checksum:
                self.logger.error(
                    "Checksum mismatch",
                    dataset_name=name,
                    version=version,
                    expected_checksum=manifest.checksum,
                    computed_checksum=computed_checksum,
                )
                raise ValueError(
                    f"Checksum mismatch for dataset {name} version {version}. "
                    f"Dataset may have been corrupted or modified."
                )
            
            self.logger.info(
                "Checksum verified",
                dataset_name=name,
                version=version,
                checksum=manifest.checksum,
            )
        
        # Build metadata
        metadata = DatasetMetadata(
            dataset_name=manifest.dataset_name,
            version=manifest.version,
            num_samples=manifest.num_samples,
            categories=manifest.categories,
            checksum=manifest.checksum,
            sampling_method="full",
            evaluation_config=manifest.evaluation_config,
        )
        
        self.logger.info(
            "Loaded processed dataset",
            dataset_name=name,
            version=version,
            num_samples=len(data),
        )
        
        return data, metadata

    def sample_dataset(
        self,
        data: List[Dict[str, Any]],
        config: SamplingConfig,
        run_id: str,
        dataset_version: str,
    ) -> tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Sample from a dataset with the given configuration.
        
        Supports:
        - Full evaluation (all samples)
        - Stratified sampling
        - Category-based selection
        
        Args:
            data: Full dataset
            config: Sampling configuration
            run_id: Run identifier for seed generation
            dataset_version: Dataset version for seed generation
            
        Returns:
            Tuple of (sampled data, sampling info)
        """
        seed = config.generate_seed(run_id, dataset_version)
        random.seed(seed)
        
        sampling_info = {
            "method": config.method,
            "seed": seed,
            "original_size": len(data),
        }
        
        if config.method == "full":
            # Return all data
            sampling_info["sample_size"] = len(data)
            return data, sampling_info
        
        elif config.method == "stratified":
            # Stratified sampling: maintain category proportions
            sample_size = config.sample_size or len(data)
            sample_size = min(sample_size, len(data))
            
            # Group by category
            categories: Dict[str, List[Dict[str, Any]]] = {}
            for sample in data:
                cat = sample.get("category", "unknown")
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append(sample)
            
            # Sample proportionally from each category
            sampled = []
            for cat, samples in categories.items():
                proportion = len(samples) / len(data)
                cat_sample_size = max(1, int(sample_size * proportion))
                cat_sample_size = min(cat_sample_size, len(samples))
                
                sampled.extend(random.sample(samples, cat_sample_size))
            
            # Fill remaining slots randomly if needed
            if len(sampled) < sample_size:
                remaining = [s for s in data if s not in sampled]
                sampled.extend(random.sample(remaining, sample_size - len(sampled)))
            
            sampling_info["sample_size"] = len(sampled)
            sampling_info["categories"] = list(categories.keys())
            
            return sampled, sampling_info
        
        elif config.method == "category_based":
            # Category-based selection: only samples from specified categories
            if not config.categories:
                raise ValueError("Categories must be specified for category_based sampling")
            
            filtered = [
                s for s in data 
                if s.get("category") in config.categories
            ]
            
            sample_size = config.sample_size or len(filtered)
            sample_size = min(sample_size, len(filtered))
            
            sampled = random.sample(filtered, sample_size)
            
            sampling_info["sample_size"] = len(sampled)
            sampling_info["selected_categories"] = config.categories
            
            return sampled, sampling_info
        
        else:
            raise ValueError(f"Unknown sampling method: {config.method}")

    def register_dataset(
        self,
        name: str,
        version: str,
        checksum: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Register a dataset version in the registry.
        
        Args:
            name: Dataset name
            version: Version string
            checksum: Dataset checksum
            metadata: Optional metadata
        """
        self._registry.add_dataset(name, version)
        self._save_registry()
        
        self.logger.info(
            "Registered dataset",
            dataset_name=name,
            version=version,
            checksum=checksum,
        )

    def get_dataset_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a dataset.
        
        Args:
            name: Dataset name
            
        Returns:
            Dictionary with dataset information or None if not found
        """
        latest_version = self._registry.get_latest_version(name)
        if latest_version is None:
            return None
        
        # Try to load manifest
        try:
            version_dir = self.processed_path / f"v{latest_version.lstrip('v')}"
            manifest_file = version_dir / "manifest.json"
            
            if manifest_file.exists():
                with open(manifest_file, "r") as f:
                    manifest_data = json.load(f)
                
                return {
                    "name": name,
                    "latest_version": latest_version,
                    "available_versions": self._registry.get_available_versions(name),
                    "num_samples": manifest_data.get("num_samples"),
                    "checksum": manifest_data.get("checksum"),
                    "categories": manifest_data.get("categories", []),
                }
        except Exception as e:
            self.logger.warning(
                "Failed to load dataset info",
                dataset_name=name,
                error=str(e),
            )
        
        return {
            "name": name,
            "latest_version": latest_version,
            "available_versions": self._registry.get_available_versions(name),
        }

    def list_datasets(self) -> List[str]:
        """
        List all available datasets.
        
        Returns:
            List of dataset names
        """
        return list(self._registry.datasets.keys())


class EvaluationDataset:
    """
    Interface for evaluation datasets.
    
    Provides a standardized interface for the orchestrator to
    access datasets with ground truth when available.
    """

    def __init__(
        self,
        data: List[Dict[str, Any]],
        metadata: DatasetMetadata,
    ):
        """
        Initialize evaluation dataset.
        
        Args:
            data: Dataset samples
            metadata: Dataset metadata
        """
        self._data = data
        self._metadata = metadata
        self._index = 0

    def __iter__(self) -> Iterator[Dict[str, Any]]:
        """Iterate over dataset samples."""
        return iter(self._data)

    def __len__(self) -> int:
        """Get number of samples."""
        return len(self._data)

    def get_ground_truth(self, sample_id: str) -> Optional[str]:
        """
        Get ground truth for a sample.
        
        Args:
            sample_id: Sample identifier
            
        Returns:
            Ground truth string or None if not available
        """
        for sample in self._data:
            if sample.get("sample_id") == sample_id:
                return sample.get("ground_truth")
        return None

    def get_sample(self, sample_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a sample by ID.
        
        Args:
            sample_id: Sample identifier
            
        Returns:
            Sample dictionary or None if not found
        """
        for sample in self._data:
            if sample.get("sample_id") == sample_id:
                return sample
        return None

    @property
    def metadata(self) -> DatasetMetadata:
        """Get dataset metadata."""
        return self._metadata

    @property
    def prompts(self) -> List[str]:
        """Get list of prompts from dataset."""
        return [
            sample.get("prompt", sample.get("base_prompt", ""))
            for sample in self._data
        ]


# Global dataset loader instance
_dataset_loader: Optional[DatasetLoader] = None


def get_dataset_loader() -> DatasetLoader:
    """Get the global dataset loader instance."""
    global _dataset_loader
    if _dataset_loader is None:
        _dataset_loader = DatasetLoader()
    return _dataset_loader
