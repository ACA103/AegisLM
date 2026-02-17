"""
Model Registry and Abstraction Layer

Provides interface for model execution with support for multiple backends.
Enables lazy loading and model switching via configuration.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.core.exceptions import (
    DeviceError,
    GenerationError,
    ModelLoadingError,
    ModelNotFoundError,
)


class ModelResponse(BaseModel):
    """Response schema from model generation."""

    text: str = Field(description="Generated text output")
    token_probs: Optional[List[float]] = Field(
        default=None,
        description="Probability distribution over tokens (if available)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata from generation"
    )
    model_name: str = Field(description="Name of the model that generated the response")
    model_version: str = Field(description="Version of the model")
    generation_time_ms: float = Field(description="Time taken for generation in milliseconds")
    token_count: int = Field(description="Number of tokens generated")


class GenerationConfig(BaseModel):
    """Configuration for text generation."""

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature"
    )
    max_tokens: int = Field(
        default=512,
        ge=1,
        le=4096,
        description="Maximum tokens to generate"
    )
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Nucleus sampling top-p"
    )
    top_k: int = Field(
        default=50,
        ge=0,
        description="Top-k sampling parameter"
    )
    repeat_penalty: float = Field(
        default=1.0,
        ge=1.0,
        le=2.0,
        description="Repetition penalty"
    )
    stop_sequences: Optional[List[str]] = Field(
        default=None,
        description="Stop sequences to terminate generation"
    )


class BaseModelExecutor(ABC):
    """
    Abstract base class for model executors.
    
    All model implementations must inherit from this class
    and implement the generate method.
    """

    def __init__(
        self,
        model_name: str,
        model_version: str = "latest",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
    ):
        self.model_name = model_name
        self.model_version = model_version
        self.device = device or settings.device
        self.cache_dir = cache_dir or settings.model_cache_dir
        self._model = None
        self._tokenizer = None
        self._is_loaded = False

    @abstractmethod
    async def load(self) -> None:
        """Load the model and tokenizer into memory."""
        pass

    @abstractmethod
    async def unload(self) -> None:
        """Unload the model from memory."""
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> ModelResponse:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt text
            config: Generation configuration
            
        Returns:
            ModelResponse with generated text and metadata
        """
        pass

    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded in memory."""
        return self._is_loaded

    async def ensure_loaded(self) -> None:
        """Ensure model is loaded, lazy loading if necessary."""
        if not self._is_loaded:
            await self.load()

    async def __aenter__(self) -> "BaseModelExecutor":
        """Async context manager entry."""
        await self.ensure_loaded()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit."""
        await self.unload()


class TransformersExecutor(BaseModelExecutor):
    """
    HuggingFace Transformers executor.
    
    Uses model.generate() instead of pipeline() for probability access.
    """

    def __init__(
        self,
        model_name: str,
        model_version: str = "latest",
        device: Optional[str] = None,
        cache_dir: Optional[str] = None,
        torch_dtype: Optional[str] = "bfloat16",
    ):
        super().__init__(model_name, model_version, device, cache_dir)
        self.torch_dtype = torch_dtype

    async def load(self) -> None:
        """Load model and tokenizer using HuggingFace Transformers."""
        try:
            # Import here to avoid heavy import at module level
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Determine dtype
            dtype_map = {
                "float32": torch.float32,
                "float16": torch.float16,
                "bfloat16": torch.bfloat16,
            }
            torch_dtype = dtype_map.get(self.torch_dtype, torch.bfloat16)

            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                trust_remote_code=True,
            )

            # Set padding token if not set
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token

            # Load model
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir,
                torch_dtype=torch_dtype,
                device_map=self.device,
                trust_remote_code=True,
            )

            self._model.eval()
            self._is_loaded = True

        except ImportError as e:
            raise ModelLoadingError(
                self.model_name,
                f"Missing required package: {e}"
            )
        except Exception as e:
            raise ModelLoadingError(
                self.model_name,
                str(e)
            )

    async def unload(self) -> None:
        """Unload model and tokenizer from memory."""
        import torch

        if self._model is not None:
            del self._model
            self._model = None

        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        # Clear CUDA cache if using CUDA
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        self._is_loaded = False

    async def generate(
        self,
        prompt: str,
        config: Optional[GenerationConfig] = None
    ) -> ModelResponse:
        """Generate text using Transformers model."""
        import time
        import torch
        from transformers import GenerationConfig as HFGenerationConfig

        await self.ensure_loaded()

        if config is None:
            config = GenerationConfig(
                temperature=settings.default_temperature,
                max_tokens=settings.default_max_tokens,
            )

        start_time = time.perf_counter()

        try:
            # Tokenize input
            inputs = self._tokenizer(
                prompt,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=2048,
            ).to(self.device)

            # Prepare generation config
            hf_config = HFGenerationConfig(
                temperature=config.temperature,
                max_new_tokens=config.max_tokens,
                top_p=config.top_p,
                top_k=config.top_k,
                repetition_penalty=config.repeat_penalty,
                do_sample=config.temperature > 0,
                eos_token_id=self._tokenizer.eos_token_id,
                pad_token_id=self._tokenizer.pad_token_id,
            )

            # Generate
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    generation_config=hf_config,
                    output_scores=True,
                    return_dict_in_generate=True,
                )

            # Extract generated text
            generated_tokens = outputs.sequences[0][inputs.input_ids.shape[1]:]
            generated_text = self._tokenizer.decode(
                generated_tokens,
                skip_special_tokens=True
            )

            # Calculate token probabilities if available
            token_probs = None
            if outputs.scores and len(outputs.scores) > 0:
                token_probs = []
                for score in outputs.scores:
                    probs = torch.softmax(score, dim=-1)
                    # Get probability of generated token
                    token_idx = generated_tokens[len(token_probs)] if len(token_probs) < len(generated_tokens) else 0
                    if token_idx < probs.shape[-1]:
                        token_probs.append(float(probs[0, token_idx]))

            generation_time = (time.perf_counter() - start_time) * 1000

            return ModelResponse(
                text=generated_text,
                token_probs=token_probs,
                metadata={
                    "finish_reason": "stop" if self._tokenizer.eos_token_id in generated_tokens else "length",
                    "input_token_count": inputs.input_ids.shape[1],
                },
                model_name=self.model_name,
                model_version=self.model_version,
                generation_time_ms=generation_time,
                token_count=len(generated_tokens),
            )

        except torch.cuda.OutOfMemoryError:
            raise GenerationError(
                f"CUDA out of memory when generating text"
            )
        except Exception as e:
            raise GenerationError(f"Generation failed: {str(e)}")


class ModelRegistry:
    """
    Registry for managing model executors.
    
    Supports lazy loading and model switching.
    """

    def __init__(self):
        self._executors: Dict[str, BaseModelExecutor] = {}
        self._lock = asyncio.Lock()

    def register(
        self,
        model_name: str,
        executor: BaseModelExecutor
    ) -> None:
        """Register a model executor."""
        self._executors[model_name] = executor

    def get_executor(
        self,
        model_name: Optional[str] = None,
        executor_type: type = TransformersExecutor,
    ) -> BaseModelExecutor:
        """
        Get or create an executor for the specified model.
        
        Args:
            model_name: Name of the model (defaults to settings.default_model)
            executor_type: Type of executor to create
            
        Returns:
            Model executor instance
        """
        model_name = model_name or settings.default_model

        if model_name not in self._executors:
            self._executors[model_name] = executor_type(model_name)

        return self._executors[model_name]

    async def unload_all(self) -> None:
        """Unload all models from memory."""
        async with self._lock:
            for executor in self._executors.values():
                if executor.is_loaded:
                    await executor.unload()
            self._executors.clear()


# Global registry instance
model_registry = ModelRegistry()


async def get_model_executor(
    model_name: Optional[str] = None,
    executor_type: type = TransformersExecutor,
) -> BaseModelExecutor:
    """
    Dependency injection function for getting a model executor.
    
    Args:
        model_name: Optional model name override
        executor_type: Type of executor to use
        
    Returns:
        Configured model executor
    """
    return model_registry.get_executor(model_name, executor_type)
