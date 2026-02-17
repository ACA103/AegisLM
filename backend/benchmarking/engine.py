"""
Benchmarking Engine

Main orchestration for the AegisLM Benchmarking Engine:
- Baseline evaluation mode
- Adversarial evaluation mode
- Delta robustness computation
- Cross-model comparison
- Statistical reporting
- Benchmark artifact generation
"""

import asyncio
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from backend.benchmarking.comparison import (
    generate_comparative_report,
    generate_vulnerability_heatmap,
    rank_models,
)
from backend.benchmarking.reporter import (
    generate_benchmark_artifact,
    generate_text_report,
)
from backend.benchmarking.schemas import (
    BenchmarkConfig,
    BenchmarkMode,
    BenchmarkPerformance,
    BenchmarkResult,
    BenchmarkStatus,
    BenchmarkWeights,
    EvaluationResult,
    MetricDeltas,
    ModelBenchmarkResult,
    ModelMetrics,
    StartBenchmarkRequest,
)
from backend.benchmarking.statistics import (
    MetricStatistics,
    calculate_vulnerability_consistency,
)
from backend.core.config import settings
from backend.core.orchestrator import (
    EvaluationInput,
    EvaluationOrchestrator,
    RunStatus,
)
from backend.logging.logger import get_logger


# =============================================================================
# Benchmark Events
# =============================================================================

class BenchmarkEvent(str, Enum):
    """Observability events for benchmarking."""
    BENCHMARK_STARTED = "BENCHMARK_STARTED"
    BENCHMARK_COMPLETED = "BENCHMARK_COMPLETED"
    BENCHMARK_FAILED = "BENCHMARK_FAILED"
    MODEL_EVALUATION_STARTED = "MODEL_EVALUATION_STARTED"
    MODEL_EVALUATION_COMPLETED = "MODEL_EVALUATION_COMPLETED"
    BASELINE_COMPLETED = "BASELINE_COMPLETED"
    ADVERSARIAL_COMPLETED = "ADVERSARIAL_COMPLETED"
    DELTA_COMPUTED = "DELTA_COMPUTED"


# =============================================================================
# Benchmark Engine
# =============================================================================

class BenchmarkEngine:
    """
    Main benchmarking engine for AegisLM.
    
    Coordinates:
    - Baseline evaluation (no attacks)
    - Adversarial evaluation (full pipeline)
    - Delta robustness computation
    - Cross-model comparison
    - Artifact generation
    """
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self._orchestrator = EvaluationOrchestrator()
        self._active_benchmarks: Dict[str, asyncio.Task] = {}
    
    def _log_event(
        self,
        event: BenchmarkEvent,
        benchmark_id: str,
        **kwargs: Any
    ) -> None:
        """Log benchmark event."""
        log_data = {
            "event": event.value,
            "benchmark_id": benchmark_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        log_data.update(kwargs)
        
        if event in [BenchmarkEvent.BENCHMARK_STARTED, BenchmarkEvent.BENCHMARK_COMPLETED]:
            self.logger.info("Benchmark event", **log_data)
        elif event in [BenchmarkEvent.BENCHMARK_FAILED]:
            self.logger.error("Benchmark event", **log_data)
        else:
            self.logger.debug("Benchmark event", **log_data)
    
    async def start_benchmark(
        self,
        request: StartBenchmarkRequest,
    ) -> UUID:
        """
        Start a new benchmark run.
        
        Args:
            request: Benchmark configuration
        
        Returns:
            Benchmark ID
        """
        benchmark_id = uuid.uuid4()
        benchmark_id_str = str(benchmark_id)
        
        self.logger.info(
            "Starting benchmark",
            benchmark_id=benchmark_id_str,
            models=request.models,
            dataset=request.dataset_name,
        )
        
        # Create benchmark config
        weights = request.weights or BenchmarkWeights()
        config = BenchmarkConfig(
            benchmark_id=benchmark_id,
            models=request.models,
            dataset_name=request.dataset_name,
            dataset_version=request.dataset_version,
            attack_enabled=request.attack_enabled,
            mutation_depth=request.mutation_depth,
            weights=weights,
            max_concurrency=request.max_concurrency,
            max_samples=request.max_samples,
            enable_baseline=request.enable_baseline,
            enable_adversarial=request.enable_adversarial,
            attack_types=request.attack_types or ["jailbreak"],
        )
        
        # Validate config
        config.validate_config()
        
        # Start async execution
        task = asyncio.create_task(
            self._execute_benchmark(config)
        )
        self._active_benchmarks[benchmark_id_str] = task
        
        return benchmark_id
    
    async def _execute_benchmark(
        self,
        config: BenchmarkConfig,
    ) -> BenchmarkResult:
        """
        Execute the benchmark asynchronously.
        
        Args:
            config: Benchmark configuration
        
        Returns:
            Complete benchmark result
        """
        benchmark_id = config.benchmark_id
        benchmark_id_str = str(benchmark_id)
        start_time = datetime.utcnow()
        
        # Initialize result
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            dataset_name=config.dataset_name,
            dataset_version=config.dataset_version,
            models=config.models,
            status=BenchmarkStatus.RUNNING,
            results=[],
            performance=BenchmarkPerformance(),
            started_at=start_time,
            config=config.model_dump(),
        )
        
        # Log start
        self._log_event(
            BenchmarkEvent.BENCHMARK_STARTED,
            benchmark_id_str,
            models=config.models,
            dataset=config.dataset_name,
        )
        
        try:
            # Evaluate each model
            for model_name in config.models:
                self._log_event(
                    BenchmarkEvent.MODEL_EVALUATION_STARTED,
                    benchmark_id_str,
                    model=model_name,
                )
                
                model_start_time = time.time()
                
                # Evaluate model
                model_result = await self._evaluate_model(
                    config=config,
                    model_name=model_name,
                    benchmark_id=benchmark_id_str,
                )
                
                model_time = time.time() - model_start_time
                
                # Update performance tracking
                result.performance.time_per_model_seconds[model_name] = model_time
                result.performance.sample_counts[model_name] = (
                    model_result.adversarial.sample_count if model_result.adversarial else 0
                )
                result.performance.failure_rates[model_name] = (
                    model_result.adversarial.failure_rate if model_result.adversarial else 1.0
                )
                
                result.results.append(model_result)
                
                self._log_event(
                    BenchmarkEvent.MODEL_EVALUATION_COMPLETED,
                    benchmark_id_str,
                    model=model_name,
                    time_seconds=model_time,
                )
            
            # Compute rankings (if multiple models)
            if len(config.models) > 1:
                result.rankings = rank_models(result.results)
                
                # Generate vulnerability heatmap
                result.vulnerability_heatmap = generate_vulnerability_heatmap(
                    result.results,
                    config.attack_types,
                )
            
            # Mark as completed
            result.status = BenchmarkStatus.COMPLETED
            result.completed_at = datetime.utcnow()
            
            # Generate artifact
            artifact_path = generate_benchmark_artifact(result)
            self.logger.info(
                "Benchmark artifact saved",
                benchmark_id=benchmark_id_str,
                path=artifact_path,
            )
            
            # Log completion
            self._log_event(
                BenchmarkEvent.BENCHMARK_COMPLETED,
                benchmark_id_str,
                models=config.models,
                completed_at=result.completed_at.isoformat(),
            )
            
        except Exception as e:
            result.status = BenchmarkStatus.FAILED
            result.error = str(e)
            result.completed_at = datetime.utcnow()
            
            self.logger.error(
                "Benchmark failed",
                benchmark_id=benchmark_id_str,
                error=str(e),
            )
            
            self._log_event(
                BenchmarkEvent.BENCHMARK_FAILED,
                benchmark_id_str,
                error=str(e),
            )
        
        finally:
            # Clean up active benchmark
            self._active_benchmarks.pop(benchmark_id_str, None)
        
        return result
    
    async def _evaluate_model(
        self,
        config: BenchmarkConfig,
        model_name: str,
        benchmark_id: str,
    ) -> ModelBenchmarkResult:
        """
        Evaluate a single model.
        
        Args:
            config: Benchmark configuration
            model_name: Name of the model to evaluate
            benchmark_id: Benchmark ID for logging
        
        Returns:
            Complete benchmark result for the model
        """
        model_result = ModelBenchmarkResult(model_name=model_name)
        
        # Create sampling config if max_samples is set
        sampling_config = None
        if config.max_samples:
            sampling_config = {
                "method": "random",
                "sample_size": config.max_samples,
            }
        
        # Run baseline evaluation
        if config.enable_baseline:
            baseline_result = await self._run_evaluation(
                model_name=model_name,
                config=config,
                mode=BenchmarkMode.BASELINE,
                attack_enabled=False,
                benchmark_id=benchmark_id,
                sampling_config=sampling_config,
            )
            model_result.baseline = baseline_result
            model_result.baseline_robustness = baseline_result.metrics.robustness
            
            self._log_event(
                BenchmarkEvent.BASELINE_COMPLETED,
                benchmark_id,
                model=model_name,
                robustness=model_result.baseline_robustness,
            )
        
        # Run adversarial evaluation
        if config.enable_adversarial:
            adversarial_result = await self._run_evaluation(
                model_name=model_name,
                config=config,
                mode=BenchmarkMode.ADVERSARIAL,
                attack_enabled=config.attack_enabled,
                benchmark_id=benchmark_id,
                sampling_config=sampling_config,
            )
            model_result.adversarial = adversarial_result
            model_result.adversarial_robustness = adversarial_result.metrics.robustness
            
            self._log_event(
                BenchmarkEvent.ADVERSARIAL_COMPLETED,
                benchmark_id,
                model=model_name,
                robustness=model_result.adversarial_robustness,
            )
        
        # Compute deltas and derived metrics
        if model_result.baseline and model_result.adversarial:
            model_result.deltas = self._compute_deltas(
                baseline=model_result.baseline,
                adversarial=model_result.adversarial,
            )
            
            # Compute delta robustness
            # ΔR = R_base - R_adv
            model_result.delta_robustness = (
                model_result.baseline_robustness - model_result.adversarial_robustness
            )
            
            # Compute Robustness Stability Index (RSI)
            # RSI = R_adv / R_base
            if model_result.baseline_robustness and model_result.baseline_robustness > 0:
                model_result.robustness_stability_index = (
                    model_result.adversarial_robustness / model_result.baseline_robustness
                )
            else:
                model_result.robustness_stability_index = 0.0
            
            # Compute Vulnerability Index (VI)
            # VI = delta_R / R_base
            if model_result.baseline_robustness and model_result.baseline_robustness > 0:
                model_result.vulnerability_index = (
                    model_result.delta_robustness / model_result.baseline_robustness
                )
            else:
                model_result.vulnerability_index = 0.0
            
            self._log_event(
                BenchmarkEvent.DELTA_COMPUTED,
                benchmark_id,
                model=model_name,
                delta_robustness=model_result.delta_robustness,
                rsi=model_result.robustness_stability_index,
                vi=model_result.vulnerability_index,
            )
        
        return model_result
    
    async def _run_evaluation(
        self,
        model_name: str,
        config: BenchmarkConfig,
        mode: BenchmarkMode,
        attack_enabled: bool,
        benchmark_id: str,
        sampling_config: Optional[Dict[str, Any]] = None,
    ) -> EvaluationResult:
        """
        Run a single evaluation (baseline or adversarial).
        
        Args:
            model_name: Model to evaluate
            config: Benchmark config
            mode: Evaluation mode
            attack_enabled: Whether to enable attacks
            benchmark_id: Benchmark ID
            sampling_config: Optional sampling config
        
        Returns:
            Evaluation result
        """
        # Create evaluation input
        eval_input = EvaluationInput(
            model_name=model_name,
            dataset_name=config.dataset_name,
            dataset_version=config.dataset_version,
            weights={
                "hallucination": config.weights.hallucination,
                "toxicity": config.weights.toxicity,
                "bias": config.weights.bias,
                "confidence": config.weights.confidence,
            },
            mutation_depth=config.mutation_depth if attack_enabled else 0,
            attack_types=config.attack_types if attack_enabled else [],
            max_concurrency=config.max_concurrency,
            sampling_config=sampling_config,
        )
        
        # Run evaluation using orchestrator
        output = await self._orchestrator.start_run(eval_input)
        
        # Wait for completion
        run_id = output.run_id
        
        # Poll for completion (in production, this would be async callback)
        max_wait = 300  # 5 minutes
        waited = 0
        poll_interval = 1
        
        while waited < max_wait:
            status = await self._orchestrator.get_run_status(run_id)
            
            if status and status.status in [RunStatus.COMPLETED, RunStatus.FAILED]:
                break
            
            await asyncio.sleep(poll_interval)
            waited += poll_interval
        
        # Get final status
        final_status = await self._orchestrator.get_run_status(run_id)
        
        if final_status and final_status.status == RunStatus.COMPLETED:
            # Extract metrics from output
            metrics = ModelMetrics(
                hallucination=final_status.metrics.get("hallucination", 0.5),
                toxicity=final_status.metrics.get("toxicity", 0.5),
                bias=final_status.metrics.get("bias", 0.5),
                confidence=final_status.metrics.get("confidence", 0.5),
                robustness=final_status.metrics.get("robustness", 0.5),
            )
            
            # Get standard deviations if available
            if final_status.metrics:
                metrics.std_hallucination = final_status.metrics.get("std_hallucination")
                metrics.std_toxicity = final_status.metrics.get("std_toxicity")
                metrics.std_bias = final_status.metrics.get("std_bias")
                metrics.std_confidence = final_status.metrics.get("std_confidence")
            
            return EvaluationResult(
                model_name=model_name,
                mode=mode,
                metrics=metrics,
                sample_count=final_status.metrics.get("total_samples", 0),
                failure_rate=final_status.metrics.get("failed_samples", 0) / max(final_status.metrics.get("total_samples", 1), 1),
                mean_latency_ms=final_status.performance.get("mean_latency_ms"),
                total_time_seconds=final_status.performance.get("total_time_seconds"),
            )
        else:
            # Return default result on failure
            return EvaluationResult(
                model_name=model_name,
                mode=mode,
                metrics=ModelMetrics(
                    hallucination=0.5,
                    toxicity=0.5,
                    bias=0.5,
                    confidence=0.5,
                    robustness=0.5,
                ),
                sample_count=0,
                failure_rate=1.0,
            )
    
    def _compute_deltas(
        self,
        baseline: EvaluationResult,
        adversarial: EvaluationResult,
    ) -> MetricDeltas:
        """
        Compute deltas between baseline and adversarial.
        
        Args:
            baseline: Baseline evaluation result
            adversarial: Adversarial evaluation result
        
        Returns:
            MetricDeltas with computed differences
        """
        return MetricDeltas(
            hallucination_delta=adversarial.metrics.hallucination - baseline.metrics.hallucination,
            toxicity_delta=adversarial.metrics.toxicity - baseline.metrics.toxicity,
            bias_delta=adversarial.metrics.bias - baseline.metrics.bias,
            confidence_delta=adversarial.metrics.confidence - baseline.metrics.confidence,
            robustness_delta=baseline.metrics.robustness - adversarial.metrics.robustness,
        )
    
    async def get_benchmark_status(
        self,
        benchmark_id: str,
    ) -> Optional[BenchmarkResult]:
        """
        Get status of a benchmark.
        
        Args:
            benchmark_id: Benchmark ID
        
        Returns:
            Benchmark result if found, None otherwise
        """
        # Check if benchmark is active
        if benchmark_id in self._active_benchmarks:
            task = self._active_benchmarks[benchmark_id]
            
            if not task.done():
                # Benchmark is still running
                # For now, return a partial result
                return BenchmarkResult(
                    benchmark_id=UUID(benchmark_id),
                    dataset_name="",
                    dataset_version="",
                    models=[],
                    status=BenchmarkStatus.RUNNING,
                    results=[],
                    performance=BenchmarkPerformance(),
                    started_at=datetime.utcnow(),
                )
            else:
                # Benchmark completed, get result
                return await task
        
        # Try to load from artifact
        from backend.benchmarking.reporter import load_benchmark_artifact
        
        artifact = load_benchmark_artifact(benchmark_id)
        
        if artifact:
            # Reconstruct BenchmarkResult from artifact
            # For simplicity, just return None - in production, parse the artifact
            pass
        
        return None
    
    async def cancel_benchmark(
        self,
        benchmark_id: str,
    ) -> bool:
        """
        Cancel a running benchmark.
        
        Args:
            benchmark_id: Benchmark ID
        
        Returns:
            True if cancelled, False otherwise
        """
        if benchmark_id in self._active_benchmarks:
            task = self._active_benchmarks[benchmark_id]
            task.cancel()
            
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            self.logger.info("Benchmark cancelled", benchmark_id=benchmark_id)
            return True
        
        return False


# =============================================================================
# Global Instance
# =============================================================================

_benchmark_engine: Optional[BenchmarkEngine] = None


def get_benchmark_engine() -> BenchmarkEngine:
    """
    Get the global benchmark engine instance.
    
    Returns:
        BenchmarkEngine singleton
    """
    global _benchmark_engine
    if _benchmark_engine is None:
        _benchmark_engine = BenchmarkEngine()
    return _benchmark_engine


__all__ = [
    "BenchmarkEngine",
    "BenchmarkEvent",
    "get_benchmark_engine",
]
