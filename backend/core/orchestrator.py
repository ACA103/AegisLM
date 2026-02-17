"""
Evaluation Orchestrator - Production Grade

Manages the full lifecycle of evaluation runs, coordinating between:
- Attacker agent
- Mutation engine
- Model executor
- Defender agent
- Judge agent
- Scoring aggregator
- Database persistence

This is a production-grade async pipeline with:
- Concurrency control
- Deterministic configuration
- Retry logic
- Observability
- Performance tracking
"""

import asyncio
import hashlib
import json
import time
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agents.attacker import AttackEngine, AttackRequest, get_attack_engine
from agents.defender import DefenderEngine, DefenderRequest, get_defender_engine
from agents.judge import JudgeEngine, JudgeRequest, get_judge_engine
from agents.mutation import MutationRequest, get_mutation_engine
from backend.core.config import settings
from backend.core.dataset_loader import (
    DatasetLoader,
    EvaluationDataset,
    SamplingConfig,
    get_dataset_loader,
)
from backend.core.dataset_schemas import DatasetMetadata
from backend.core.exceptions import EvaluationError, EvaluationTimeoutError
from backend.db.models import EvaluationResult, EvaluationRun
from backend.db.session import get_db_context
from backend.logging.logger import get_logger
from backend.scoring.aggregator import ScoreAggregator, get_aggregator


# =============================================================================
# Enums
# =============================================================================

class RunStatus(str, Enum):
    """Status of an evaluation run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class LogEvent(str, Enum):
    """Observability log events."""
    RUN_STARTED = "RUN_STARTED"
    RUN_COMPLETED = "RUN_COMPLETED"
    RUN_FAILED = "RUN_FAILED"
    SAMPLE_STARTED = "SAMPLE_STARTED"
    SAMPLE_COMPLETED = "SAMPLE_COMPLETED"
    SAMPLE_FAILED = "SAMPLE_FAILED"
    ATTACK_COMPLETED = "ATTACK_COMPLETED"
    MUTATION_COMPLETED = "MUTATION_COMPLETED"
    MODEL_COMPLETED = "MODEL_COMPLETED"
    DEFENDER_COMPLETED = "DEFENDER_COMPLETED"
    JUDGE_COMPLETED = "JUDGE_COMPLETED"


# =============================================================================
# Run Configuration
# =============================================================================

class RunConfig(BaseModel):
    """
    Deterministic run configuration.
    
    All fields are used to generate a config hash for reproducibility.
    """
    run_id: UUID = Field(description="Unique run identifier")
    model_name: str = Field(description="Name of the model to evaluate")
    model_version: str = Field(default="latest", description="Model version")
    dataset_name: str = Field(description="Dataset name")
    dataset_version: str = Field(description="Dataset version")
    weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "hallucination": settings.hallucination_weight,
            "toxicity": settings.toxicity_weight,
            "bias": settings.bias_weight,
            "confidence": settings.confidence_weight,
        },
        description="Scoring weights"
    )
    mutation_depth: int = Field(default=2, ge=0, le=10, description="Mutation depth")
    attack_types: List[str] = Field(
        default_factory=list,
        description="List of attack types to use"
    )
    max_concurrency: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum concurrent samples"
    )
    max_retries: int = Field(
        default=2,
        ge=0,
        le=5,
        description="Maximum retries for model inference"
    )
    sampling_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Dataset sampling configuration"
    )

    def get_config_hash(self) -> str:
        """Generate SHA256 hash of configuration for reproducibility."""
        config_dict = self.model_dump()
        # Sort keys for deterministic hashing
        sorted_config = json.dumps(config_dict, sort_keys=True)
        return hashlib.sha256(sorted_config.encode()).hexdigest()


# =============================================================================
# Data Models
# =============================================================================

class EvaluationInput(BaseModel):
    """Input for starting an evaluation run."""

    model_name: str = Field(description="Name of the model to evaluate")
    model_version: str = Field(default="latest", description="Model version")
    dataset_name: str = Field(description="Dataset name")
    dataset_version: str = Field(description="Dataset version to use")
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional scoring weights override"
    )
    mutation_depth: int = Field(default=2, ge=0, le=10, description="Mutation depth")
    attack_types: Optional[List[str]] = Field(
        default=None,
        description="List of attack types"
    )
    max_concurrency: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Maximum concurrent samples"
    )
    sampling_config: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional sampling configuration"
    )


class EvaluationOutput(BaseModel):
    """Output of an evaluation run."""

    run_id: str = Field(description="Unique identifier for this run")
    model_name: str = Field(description="Name of the evaluated model")
    model_version: str = Field(description="Version of the evaluated model")
    dataset_version: str = Field(description="Dataset version used")
    status: RunStatus = Field(description="Final status of the run")
    composite_score: Optional[float] = Field(
        default=None,
        description="Composite robustness score (0-1)",
        ge=0.0,
        le=1.0
    )
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Individual metric scores"
    )
    performance: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics"
    )
    started_at: datetime = Field(description="When the run started")
    completed_at: Optional[datetime] = Field(
        default=None,
        description="When the run completed"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if failed"
    )


class SampleResult(BaseModel):
    """Result for a single sample."""
    sample_id: str
    attack_type: Optional[str] = None
    mutation_type: Optional[str] = None
    hallucination: Optional[float] = None
    toxicity: Optional[float] = None
    bias: Optional[float] = None
    confidence: Optional[float] = None
    robustness: Optional[float] = None
    raw_output: Optional[str] = None
    processed_prompt: Optional[str] = None
    latency_ms: Optional[float] = None
    success: bool = True
    error: Optional[str] = None


# =============================================================================
# Orchestrator Class
# =============================================================================

class EvaluationOrchestrator:
    """
    Production-grade orchestrator for evaluation pipeline.
    
    Coordinates attacker → mutation → model → defender → judge → scoring
    with full observability, concurrency control, and persistence.
    """

    def __init__(self):
        self.logger = get_logger(__name__)
        self._active_runs: Dict[str, asyncio.Task] = {}
        self._aggregator = get_aggregator()

    def _create_run_config(self, evaluation_input: EvaluationInput, run_id: UUID) -> RunConfig:
        """Create RunConfig from evaluation input."""
        return RunConfig(
            run_id=run_id,
            model_name=evaluation_input.model_name,
            model_version=evaluation_input.model_version,
            dataset_name=evaluation_input.dataset_name,
            dataset_version=evaluation_input.dataset_version,
            weights=evaluation_input.weights or {
                "hallucination": settings.hallucination_weight,
                "toxicity": settings.toxicity_weight,
                "bias": settings.bias_weight,
                "confidence": settings.confidence_weight,
            },
            mutation_depth=evaluation_input.mutation_depth,
            attack_types=evaluation_input.attack_types or ["jailbreak"],
            max_concurrency=evaluation_input.max_concurrency,
            sampling_config=evaluation_input.sampling_config,
        )

    async def _persist_run_start(self, config: RunConfig) -> None:
        """Persist run start to database."""
        try:
            async with get_db_context() as session:
                run = EvaluationRun(
                    id=config.run_id,
                    model_name=config.model_name,
                    model_version=config.model_version,
                    dataset_version=config.dataset_version,
                    status=RunStatus.PENDING.value,
                    config_hash=config.get_config_hash(),
                )
                session.add(run)
                await session.commit()
                self.logger.info("Run created in database", run_id=str(config.run_id))
        except Exception as e:
            self.logger.warning("Failed to persist run start", error=str(e))

    async def _persist_sample_result(self, result: SampleResult, run_id: UUID) -> None:
        """Persist individual sample result to database."""
        try:
            async with get_db_context() as session:
                eval_result = EvaluationResult(
                    run_id=run_id,
                    sample_id=result.sample_id,
                    attack_type=result.attack_type,
                    mutation_type=result.mutation_type,
                    hallucination=result.hallucination,
                    toxicity=result.toxicity,
                    bias=result.bias,
                    confidence=result.confidence,
                    robustness=result.robustness,
                    raw_output=result.raw_output,
                    processed_prompt=result.processed_prompt,
                    processing_time_ms=result.latency_ms,
                )
                session.add(eval_result)
                await session.commit()
        except Exception as e:
            self.logger.warning(
                "Failed to persist sample result",
                sample_id=result.sample_id,
                error=str(e)
            )

    async def _update_run_status(
        self,
        run_id: UUID,
        status: RunStatus,
        composite_score: Optional[float] = None,
        error: Optional[str] = None
    ) -> None:
        """Update run status in database."""
        try:
            async with get_db_context() as session:
                stmt = select(EvaluationRun).where(EvaluationRun.id == run_id)
                result = await session.execute(stmt)
                run = result.scalar_one_or_none()
                
                if run:
                    run.status = status.value
                    if composite_score is not None:
                        run.composite_score = composite_score
                    if error:
                        run.status = RunStatus.FAILED.value
                    await session.commit()
        except Exception as e:
            self.logger.warning("Failed to update run status", error=str(e))

    def _log_event(
        self,
        event: LogEvent,
        run_id: str,
        sample_id: Optional[str] = None,
        **kwargs: Any
    ) -> None:
        """Log observability event."""
        log_data = {
            "event": event.value,
            "run_id": run_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if sample_id:
            log_data["sample_id"] = sample_id
        log_data.update(kwargs)
        
        if event in [LogEvent.RUN_STARTED, LogEvent.SAMPLE_COMPLETED]:
            self.logger.info(**log_data)
        elif event in [LogEvent.RUN_FAILED, LogEvent.SAMPLE_FAILED]:
            self.logger.error(**log_data)
        else:
            self.logger.debug(**log_data)

    def _get_dataset_prompts(
        self,
        dataset_name: str,
        dataset_version: Optional[str] = None,
        sampling_config: Optional[SamplingConfig] = None,
        run_id: Optional[str] = None,
    ) -> tuple[List[Dict[str, Any]], Optional[DatasetMetadata]]:
        """
        Get sample prompts from the dataset for evaluation.
        
        Returns:
            Tuple of (list of samples with prompt/id, dataset metadata)
        """
        try:
            loader = get_dataset_loader()
            
            data, metadata = loader.load_processed_dataset(
                name=dataset_name,
                version=dataset_version,
                verify_checksum=True,
            )
            
            # Apply sampling if configured
            if sampling_config and run_id:
                data, sampling_info = loader.sample_dataset(
                    data=data,
                    config=sampling_config,
                    run_id=run_id,
                    dataset_version=dataset_version or metadata.version,
                )
                self.logger.info(
                    "Dataset sampled",
                    dataset_name=dataset_name,
                    dataset_version=dataset_version or metadata.version,
                    sampling_method=sampling_config.method,
                    sample_size=len(data),
                    seed=sampling_info.get("seed"),
                )
            
            self.logger.info(
                "Loaded dataset prompts",
                dataset_name=dataset_name,
                dataset_version=dataset_version or metadata.version,
                prompt_count=len(data),
                checksum=metadata.checksum,
            )
            
            return data, metadata
            
        except FileNotFoundError as e:
            self.logger.warning(
                "Dataset not found, using fallback prompts",
                dataset_name=dataset_name,
                error=str(e),
            )
            # Fallback to sample prompts
            sample_prompts = [
                {"prompt": "Explain how to cook a meal", "sample_id": "sample_0"},
                {"prompt": "What are the benefits of exercise?", "sample_id": "sample_1"},
                {"prompt": "Tell me about the history of computers", "sample_id": "sample_2"},
                {"prompt": "How do plants grow?", "sample_id": "sample_3"},
                {"prompt": "What is the capital of France?", "sample_id": "sample_4"},
            ]
            return sample_prompts, None

    async def start_run(
        self,
        evaluation_input: EvaluationInput,
    ) -> EvaluationOutput:
        """
        Start a new evaluation run.
        
        Args:
            evaluation_input: Configuration for the evaluation
            
        Returns:
            EvaluationOutput with initial run information
        """
        run_id = uuid.uuid4()
        run_id_str = str(run_id)
        
        self.logger.info(
            "Starting evaluation run",
            run_id=run_id_str,
            model=evaluation_input.model_name,
            dataset=evaluation_input.dataset_name,
        )
        
        # Create run config
        config = self._create_run_config(evaluation_input, run_id)
        
        # Create initial output
        output = EvaluationOutput(
            run_id=run_id_str,
            model_name=evaluation_input.model_name,
            model_version=evaluation_input.model_version,
            dataset_version=evaluation_input.dataset_version,
            status=RunStatus.PENDING,
            started_at=datetime.utcnow(),
        )
        
        # Persist run start to database
        await self._persist_run_start(config)
        
        # Log observability event
        self._log_event(LogEvent.RUN_STARTED, run_id_str, config=config.model_dump())
        
        # Start async execution
        task = asyncio.create_task(
            self._execute_run(evaluation_input, output, config)
        )
        self._active_runs[run_id_str] = task
        
        return output

    async def _execute_run(
        self,
        evaluation_input: EvaluationInput,
        output: EvaluationOutput,
        config: RunConfig,
    ) -> EvaluationOutput:
        """
        Execute the evaluation run asynchronously with full pipeline.
        """
        run_id = config.run_id
        run_id_str = str(run_id)
        output.status = RunStatus.RUNNING
        
        # Update status in DB
        await self._update_run_status(run_id, RunStatus.RUNNING)
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(config.max_concurrency)
        
        # Track performance metrics
        start_time = time.time()
        sample_results: List[SampleResult] = []
        failed_count = 0
        
        try:
            # =========================================================================
            # Load datasets
            # =========================================================================
            self.logger.info("Loading dataset", run_id=run_id_str)
            
            sampling_config = None
            if evaluation_input.sampling_config:
                sampling_config = SamplingConfig(**evaluation_input.sampling_config)
            
            samples, metadata = self._get_dataset_prompts(
                dataset_name=evaluation_input.dataset_name,
                dataset_version=evaluation_input.dataset_version,
                sampling_config=sampling_config,
                run_id=run_id_str,
            )
            
            # Get agent engines
            attacker_engine = get_attack_engine()
            mutation_engine = get_mutation_engine()
            defender_engine = get_defender_engine()
            judge_engine = get_judge_engine()
            
            # =========================================================================
            # Process samples with bounded concurrency
            # =========================================================================
            async def process_sample(sample: Dict[str, Any], index: int) -> SampleResult:
                """Process a single sample through the full pipeline."""
                sample_id = sample.get("sample_id", f"sample_{index}")
                base_prompt = sample.get("prompt", sample.get("base_prompt", ""))
                
                self._log_event(
                    LogEvent.SAMPLE_STARTED,
                    run_id_str,
                    sample_id=sample_id,
                    prompt_length=len(base_prompt)
                )
                
                sample_start_time = time.time()
                
                try:
                    # Use semaphore for concurrency control
                    async with semaphore:
                        # =================================================================
                        # Step 1: Attack Generation
                        # =================================================================
                        attack_request = AttackRequest(
                            run_id=run_id,
                            sample_id=sample_id,
                            base_prompt=base_prompt,
                            attack_type=config.attack_types[0] if config.attack_types else "jailbreak",
                            temperature=0.7,
                            chain_depth=2,
                        )
                        
                        attack_response = await attacker_engine.execute(attack_request)
                        
                        self._log_event(
                            LogEvent.ATTACK_COMPLETED,
                            run_id_str,
                            sample_id=sample_id,
                            attack_type=attack_response.attack_type,
                        )
                        
                        # =================================================================
                        # Step 2: Mutation
                        # =================================================================
                        mutation_request = MutationRequest(
                            run_id=run_id,
                            sample_id=sample_id,
                            base_prompt=attack_response.mutated_prompt,
                            attack_type=attack_response.attack_type,
                            mutation_depth=config.mutation_depth,
                        )
                        
                        mutation_response = await mutation_engine.mutate(mutation_request)
                        
                        self._log_event(
                            LogEvent.MUTATION_COMPLETED,
                            run_id_str,
                            sample_id=sample_id,
                            mutation_depth=mutation_response.mutation_depth,
                        )
                        
                        # =================================================================
                        # Step 3: Model Execution (with retry)
                        # =================================================================
                        model_output = None
                        for retry in range(config.max_retries + 1):
                            try:
                                # TODO: Replace with actual model executor
                                # Placeholder: In production, this would call the actual model
                                model_output = await self._execute_model(
                                    mutation_response.mutated_prompt,
                                    evaluation_input.model_name,
                                )
                                break
                            except Exception as e:
                                if retry < config.max_retries:
                                    self.logger.warning(
                                        "Model inference failed, retrying",
                                        sample_id=sample_id,
                                        retry=retry + 1,
                                        error=str(e)
                                    )
                                    await asyncio.sleep(0.5 * (retry + 1))
                                else:
                                    raise
                        
                        self._log_event(
                            LogEvent.MODEL_COMPLETED,
                            run_id_str,
                            sample_id=sample_id,
                        )
                        
                        # =================================================================
                        # Step 4: Defender Evaluation
                        # =================================================================
                        defender_request = DefenderRequest(
                            run_id=run_id,
                            sample_id=sample_id,
                            model_output=model_output,
                            attack_type=attack_response.attack_type,
                            base_prompt=mutation_response.mutated_prompt,
                        )
                        
                        defense_output = await defender_engine.evaluate(defender_request)
                        
                        self._log_event(
                            LogEvent.DEFENDER_COMPLETED,
                            run_id_str,
                            sample_id=sample_id,
                            risk_score=defense_output.risk_score,
                        )
                        
                        # =================================================================
                        # Step 5: Judge Evaluation
                        # =================================================================
                        judge_request = JudgeRequest(
                            run_id=run_id,
                            sample_id=sample_id,
                            prompt=mutation_response.mutated_prompt,
                            model_output=model_output,
                            defender_risk_score=defense_output.risk_score,
                            defender_toxicity_score=defense_output.toxicity_score,
                            token_probs=None,
                            temperature=0.7,
                        )
                        
                        judge_output = await judge_engine.evaluate(judge_request)
                        
                        self._log_event(
                            LogEvent.JUDGE_COMPLETED,
                            run_id_str,
                            sample_id=sample_id,
                            hallucination=judge_output.hallucination_score,
                            bias=judge_output.bias_score,
                        )
                        
                        # =================================================================
                        # Calculate robustness for this sample
                        # =================================================================
                        robustness = self._aggregator.calculate_composite(
                            hallucination=judge_output.hallucination_score,
                            toxicity=defense_output.toxicity_score,
                            bias=judge_output.bias_score,
                            confidence=judge_output.confidence_score,
                        )
                        
                        latency_ms = (time.time() - sample_start_time) * 1000
                        
                        # Build result
                        result = SampleResult(
                            sample_id=sample_id,
                            attack_type=attack_response.attack_type,
                            mutation_type="-".join(mutation_response.mutation_trace) if mutation_response.mutation_trace else None,
                            hallucination=judge_output.hallucination_score,
                            toxicity=defense_output.toxicity_score,
                            bias=judge_output.bias_score,
                            confidence=judge_output.confidence_score,
                            robustness=robustness,
                            raw_output=model_output,
                            processed_prompt=mutation_response.mutated_prompt,
                            latency_ms=latency_ms,
                            success=True,
                        )
                        
                        self._log_event(
                            LogEvent.SAMPLE_COMPLETED,
                            run_id_str,
                            sample_id=sample_id,
                            latency_ms=latency_ms,
                            robustness=robustness,
                        )
                        
                        return result
                        
                except Exception as e:
                    latency_ms = (time.time() - sample_start_time) * 1000
                    self.logger.error(
                        "Sample processing failed",
                        run_id=run_id_str,
                        sample_id=sample_id,
                        error=str(e)
                    )
                    
                    self._log_event(
                        LogEvent.SAMPLE_FAILED,
                        run_id_str,
                        sample_id=sample_id,
                        error=str(e),
                    )
                    
                    return SampleResult(
                        sample_id=sample_id,
                        latency_ms=latency_ms,
                        success=False,
                        error=str(e),
                    )
            
            # Process all samples
            tasks = [process_sample(sample, idx) for idx, sample in enumerate(samples)]
            sample_results = await asyncio.gather(*tasks)
            
            # Count failures
            failed_count = sum(1 for r in sample_results if not r.success)
            
            # =========================================================================
            # Aggregate Metrics
            # =========================================================================
            successful_results = [r for r in sample_results if r.success]
            
            if successful_results:
                # Calculate means
                n = len(successful_results)
                
                mean_hallucination = sum(r.hallucination or 0 for r in successful_results) / n
                mean_toxicity = sum(r.toxicity or 0 for r in successful_results) / n
                mean_bias = sum(r.bias or 0 for r in successful_results) / n
                mean_confidence = sum(r.confidence or 0 for r in successful_results) / n
                mean_robustness = sum(r.robustness or 0 for r in successful_results) / n
                mean_latency = sum(r.latency_ms or 0 for r in successful_results) / n
                
                # Calculate composite score
                composite_score = self._aggregator.calculate_composite(
                    hallucination=mean_hallucination,
                    toxicity=mean_toxicity,
                    bias=mean_bias,
                    confidence=mean_confidence,
                )
                
                # Update output
                output.composite_score = composite_score
                output.metrics = {
                    "hallucination": mean_hallucination,
                    "toxicity": mean_toxicity,
                    "bias": mean_bias,
                    "confidence": mean_confidence,
                    "robustness": mean_robustness,
                    "total_samples": len(sample_results),
                    "successful_samples": len(successful_results),
                    "failed_samples": failed_count,
                }
                
                # Performance metrics
                total_time = time.time() - start_time
                throughput = len(sample_results) / total_time if total_time > 0 else 0
                failure_rate = failed_count / len(sample_results) if sample_results else 0
                
                output.performance = {
                    "mean_latency_ms": mean_latency,
                    "total_time_seconds": total_time,
                    "throughput_samples_per_second": throughput,
                    "failure_rate": failure_rate,
                }
                
                # Persist each sample result
                for result in sample_results:
                    await self._persist_sample_result(result, run_id)
                
                # Update run status in DB
                await self._update_run_status(run_id, RunStatus.COMPLETED, composite_score)
                
            else:
                # All samples failed
                output.error = "All samples failed processing"
                await self._update_run_status(run_id, RunStatus.FAILED, error=output.error)
            
            output.status = RunStatus.COMPLETED
            output.completed_at = datetime.utcnow()
            
            # Save artifacts
            await self._save_artifacts(output, config, metadata)
            
            # Log observability event
            self._log_event(
                LogEvent.RUN_COMPLETED,
                run_id_str,
                composite_score=output.composite_score,
                total_samples=len(sample_results),
                failed_samples=failed_count,
            )
            
            self.logger.info(
                "Evaluation run completed",
                run_id=run_id_str,
                composite_score=output.composite_score,
                total_samples=len(sample_results),
                failed_samples=failed_count,
            )
            
        except Exception as e:
            output.status = RunStatus.FAILED
            output.error = str(e)
            output.completed_at = datetime.utcnow()
            
            await self._update_run_status(run_id, RunStatus.FAILED, error=str(e))
            
            self._log_event(
                LogEvent.RUN_FAILED,
                run_id_str,
                error=str(e),
            )
            
            self.logger.error(
                "Evaluation run failed",
                run_id=run_id_str,
                error=str(e),
            )
            
        finally:
            # Clean up active run
            self._active_runs.pop(run_id_str, None)
        
        return output

    async def _execute_model(
        self,
        prompt: str,
        model_name: str,
    ) -> str:
        """
        Execute model inference.
        
        This is a placeholder. In production, this would call the actual model.
        """
        # Placeholder: In production, this would call the actual model
        # For now, simulate model execution
        await asyncio.sleep(0.05)  # Simulate inference time
        
        return f"[Model response to: {prompt[:50]}...]"

    async def _save_artifacts(
        self,
        output: EvaluationOutput,
        config: RunConfig,
        metadata: Optional[DatasetMetadata] = None,
    ) -> None:
        """Save evaluation artifacts to disk."""
        artifacts_dir = Path(settings.experiment_artifacts_path)
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_file = artifacts_dir / f"{output.run_id}.json"
        
        artifact_data = {
            "run_id": output.run_id,
            "config": config.model_dump(),
            "model_name": output.model_name,
            "model_version": output.model_version,
            "dataset_version": output.dataset_version,
            "dataset_metadata": metadata.model_dump() if metadata else None,
            "status": output.status.value,
            "composite_score": output.composite_score,
            "metrics": output.metrics,
            "performance": output.performance,
            "started_at": output.started_at.isoformat(),
            "completed_at": output.completed_at.isoformat() if output.completed_at else None,
            "error": output.error,
            "config_hash": config.get_config_hash(),
        }
        
        with open(artifact_file, "w") as f:
            json.dump(artifact_data, f, indent=2)
        
        self.logger.info(
            "Artifacts saved",
            run_id=output.run_id,
            artifact_path=str(artifact_file),
        )

    async def get_run_status(self, run_id: str) -> Optional[EvaluationOutput]:
        """Get the status of an active or completed run."""
        # Check if run is active
        if run_id in self._active_runs:
            return EvaluationOutput(
                run_id=run_id,
                status=RunStatus.RUNNING,
                started_at=datetime.utcnow(),
            )
        
        # Try to load from artifacts
        artifact_file = Path(settings.experiment_artifacts_path) / f"{run_id}.json"
        
        if artifact_file.exists():
            with open(artifact_file, "r") as f:
                data = json.load(f)
            
            return EvaluationOutput(
                run_id=data["run_id"],
                model_name=data["model_name"],
                model_version=data["model_version"],
                dataset_version=data["dataset_version"],
                status=RunStatus(data["status"]),
                composite_score=data.get("composite_score"),
                metrics=data.get("metrics", {}),
                performance=data.get("performance", {}),
                started_at=datetime.fromisoformat(data["started_at"]),
                completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
                error=data.get("error"),
            )
        
        return None

    async def cancel_run(self, run_id: str) -> bool:
        """Cancel an active run."""
        if run_id in self._active_runs:
            task = self._active_runs[run_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            await self._update_run_status(
                uuid.UUID(run_id),
                RunStatus.CANCELLED,
            )
            
            self.logger.info("Run cancelled", run_id=run_id)
            return True
        
        return False


# =============================================================================
# Global Instance and Factory
# =============================================================================

orchestrator = EvaluationOrchestrator()


async def get_orchestrator() -> EvaluationOrchestrator:
    """Dependency injection for orchestrator."""
    return orchestrator


__all__ = [
    "EvaluationOrchestrator",
    "EvaluationInput",
    "EvaluationOutput",
    "RunConfig",
    "RunStatus",
    "LogEvent",
    "SampleResult",
    "orchestrator",
    "get_orchestrator",
]
