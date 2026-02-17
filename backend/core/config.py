"""
Core Configuration Module

Environment-driven configuration system for AegisLM.
Implements settings with validation and config hash generation.
"""

import hashlib
import json
from typing import Any, Dict, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database Configuration
    database_url: str = Field(
        default="postgresql+asyncpg://aegislm:aegislm@localhost:5432/aegislm",
        description="PostgreSQL database connection URL"
    )
    
    # Redis Configuration (Optional)
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis connection URL for caching"
    )

    # Model Configuration
    default_model: str = Field(
        default="meta-llama/Llama-2-7b-hf",
        description="Default model for evaluation"
    )
    default_temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Default generation temperature"
    )
    default_max_tokens: int = Field(
        default=512,
        ge=1,
        le=4096,
        description="Default maximum tokens to generate"
    )

    # Scoring Weights (must sum to 1.0)
    hallucination_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for hallucination metric in composite score"
    )
    toxicity_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for toxicity metric in composite score"
    )
    bias_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for bias metric in composite score"
    )
    confidence_weight: float = Field(
        default=0.25,
        ge=0.0,
        le=1.0,
        description="Weight for confidence metric in composite score"
    )

    # Hallucination Detection Parameters
    hallucination_alpha: float = Field(
        default=0.5,
        description="Alpha parameter for hallucination detection threshold"
    )
    hallucination_beta: float = Field(
        default=0.3,
        description="Beta parameter for hallucination detection sensitivity"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API host address"
    )
    api_port: int = Field(
        default=8000,
        ge=1,
        le=65535,
        description="API port number"
    )
    api_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of API worker processes"
    )

    # Experiment Configuration
    experiment_artifacts_path: str = Field(
        default="experiments/runs",
        description="Path to store experiment artifacts"
    )
    max_concurrent_evaluations: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum concurrent evaluation runs"
    )

    # Logging Configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)"
    )

    # Model Configuration
    model_cache_dir: Optional[str] = Field(
        default=None,
        description="Directory for caching model weights"
    )
    device: str = Field(
        default="cuda",
        description="Device for model inference (cuda or cpu)"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    def validate_weights(self) -> None:
        """Validate that scoring weights sum to 1.0."""
        total = (
            self.hallucination_weight
            + self.toxicity_weight
            + self.bias_weight
            + self.confidence_weight
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total}"
            )

    def get_config_hash(self) -> str:
        """Generate SHA256 hash of configuration for reproducibility."""
        config_dict = {
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "hallucination_weight": self.hallucination_weight,
            "toxicity_weight": self.toxicity_weight,
            "bias_weight": self.bias_weight,
            "confidence_weight": self.confidence_weight,
            "hallucination_alpha": self.hallucination_alpha,
            "hallucination_beta": self.hallucination_beta,
            "device": self.device,
        }
        
        # Sort keys for deterministic hashing
        sorted_config = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(sorted_config.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary (excluding sensitive fields)."""
        return {
            "default_model": self.default_model,
            "default_temperature": self.default_temperature,
            "default_max_tokens": self.default_max_tokens,
            "hallucination_weight": self.hallucination_weight,
            "toxicity_weight": self.toxicity_weight,
            "bias_weight": self.bias_weight,
            "confidence_weight": self.confidence_weight,
            "hallucination_alpha": self.hallucination_alpha,
            "hallucination_beta": self.hallucination_beta,
            "api_host": self.api_host,
            "api_port": self.api_port,
            "device": self.device,
            "config_hash": self.get_config_hash(),
        }


# Global settings instance
settings = Settings()


# Initialize settings and validate on import
try:
    settings.validate_weights()
except ValueError as e:
    import warnings
    warnings.warn(f"Settings validation error: {e}")
