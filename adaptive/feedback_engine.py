"""
Feedback Engine

Closed-loop evaluation feedback system.
Implements the adaptive adversarial evaluation mode:

1. Run baseline attacks
2. Compute vulnerabilities
3. Re-weight attack probabilities
4. Re-run evaluation
5. Iterate for K rounds
6. Converge toward worst-case robustness

This transforms AegisLM from static red-team simulator into adaptive adversarial intelligence.
"""

import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from adaptive.attack_optimizer import AttackOptimizer, get_attack_optimizer
from adaptive.schemas import (
    AdaptiveConfig,
    AdaptiveEvaluationResult,
    AdaptiveIterationResult,
    AdaptiveMode,
)
from adaptive.strategy_evolution import (
    StrategyEvolution,
    get_strategy_evolution,
)
from adaptive.vulnerability_analyzer import (
    VulnerabilityAnalyzer,
    get_vulnerability_analyzer,
)
from agents.attacker.registry import list_attack_strategies
from backend.logging.logger import get_logger


class FeedbackEngine:
    """
    Closed-loop feedback engine for adaptive adversarial evaluation.
    
    Orchestrates the adaptive learning process:
    1. Initial baseline evaluation
    2. Vulnerability analysis
    3. Attack probability optimization
    4. Iterative evaluation with evolved strategies
    5. Convergence detection
    """
    
    def __init__(
        self,
        config: Optional[AdaptiveConfig] = None,
    ):
        """
        Initialize the feedback engine.
        
        Args:
            config: Adaptive configuration (uses defaults if not provided)
        """
        self.logger = get_logger(__name__)
        self._config = config or AdaptiveConfig()
        
        # Initialize components
        self._vulnerability_analyzer = VulnerabilityAnalyzer(config=self._config)
        self._attack_optimizer = AttackOptimizer(config=self._config)
        self._strategy_evolution = StrategyEvolution(config=self._config)
        
        # Track iteration results
        self._iteration_results: List[AdaptiveIterationResult] = []
        self._started_at: Optional[datetime] = None
        self._completed_at: Optional[datetime] = None
        
        # Track worst-case robustness
        self._initial_worst_case = 0.5
        self._current_worst_case = 0.5
    
    @property
    def config(self) -> AdaptiveConfig:
        """Get the adaptive configuration."""
        return self._config
    
    @property
    def is_enabled(self) -> bool:
        """Check if adaptive mode is enabled."""
        return self._config.enabled
    
    @property
    def iteration_results(self) -> List[AdaptiveIterationResult]:
        """Get iteration results."""
        return self._iteration_results.copy()
    
    def reset(self) -> None:
        """Reset the feedback engine state."""
        self._vulnerability_analyzer.clear_history()
        self._attack_optimizer.reset()
        self._strategy_evolution.reset()
        self._iteration_results = []
        self._started_at = None
        self._completed_at = None
        self._initial_worst_case = 0.5
        self._current_worst_case = 0.5
        self.logger.info("Reset feedback engine")
    
    async def run_adaptive_evaluation(
        self,
        evaluation_fn,
        attack_types: Optional[List[str]] = None,
    ) -> AdaptiveEvaluationResult:
        """
        Run adaptive adversarial evaluation.
        
        Args:
            evaluation_fn: Async function to run a single evaluation
                           Should accept: attack_type, mutation_depth
                           Should return: dict with metrics
            attack_types: Optional list of attack types to evaluate
            
        Returns:
            AdaptiveEvaluationResult with complete evaluation results
        """
        if not self._config.enabled:
            self.logger.warning("Adaptive mode is disabled, returning default result")
            return self._create_default_result()
        
        self._started_at = datetime.utcnow()
        
        # Validate config
        try:
            self._config.validate_config()
        except ValueError as e:
            self.logger.error(f"Invalid adaptive config: {e}")
            return self._create_default_result(error=str(e))
        
        # Get available attack types
        if attack_types is None:
            attack_types = list_attack_strategies()
        
        self.logger.info(
            "Starting adaptive evaluation",
            mode=self._config.mode.value,
            max_iterations=self._config.max_iterations,
            attack_types=attack_types,
        )
        
        # Initialize evaluation loop
        converged = False
        total_compute_time = 0.0
        total_samples = 0
        
        # Get initial baseline (if mode allows)
        if self._config.mode == AdaptiveMode.AGGRESSIVE:
            # Run initial baseline evaluation
            initial_metrics = await self._run_initial_baseline(
                evaluation_fn, 
                attack_types
            )
            self._initial_worst_case = initial_metrics.get("worst_case_robustness", 0.5)
        
        # Run adaptive iterations
        for iteration in range(1, self._config.max_iterations + 1):
            self.logger.info(f"Starting adaptive iteration {iteration}")
            
            iter_start_time = time.time()
            
            # Step 1: Evolve vulnerabilities using strategy evolution
            evolved_vulns = self._strategy_evolution.evolve_vulnerabilities()
            
            # Step 2: Compute vulnerabilities from recent evaluations
            recent_vulns = self._vulnerability_analyzer.compute_vulnerabilities()
            
            # Step 3: Combine with evolved vulnerabilities
            if evolved_vulns:
                combined_vulns = {
                    at: 0.5 * evolved_vulns.get(at, 0.0) + 0.5 * recent_vulns.get(at, 0.0)
                    for at in set(list(evolved_vulns.keys()) + list(recent_vulns.keys()))
                }
            else:
                combined_vulns = recent_vulns
            
            # Step 4: Compute adaptive probabilities
            selection_probs = self._attack_optimizer.compute_probabilities(
                combined_vulns,
                attack_types,
            )
            
            # Step 5: Run evaluation with adaptive probabilities
            iter_metrics = await self._run_iteration_evaluation(
                evaluation_fn,
                selection_probs,
            )
            
            iter_time = time.time() - iter_start_time
            total_compute_time += iter_time
            total_samples += iter_metrics.get("samples_evaluated", 0)
            
            # Step 6: Compute worst-case robustness
            worst_case = iter_metrics.get("worst_case_robustness", 0.5)
            mean_robustness = iter_metrics.get("mean_robustness", 0.5)
            
            # Step 7: Check convergence
            convergence_delta = abs(worst_case - self._current_worst_case)
            self._current_worst_case = worst_case
            
            # Store iteration result
            iter_result = AdaptiveIterationResult(
                iteration=iteration,
                attack_probabilities=selection_probs.probabilities,
                vulnerabilities=combined_vulns,
                worst_case_robustness=worst_case,
                mean_robustness=mean_robustness,
                convergence_delta=convergence_delta,
                compute_time_seconds=iter_time,
                samples_evaluated=iter_metrics.get("samples_evaluated", 0),
            )
            self._iteration_results.append(iter_result)
            
            self.logger.info(
                f"Completed iteration {iteration}",
                worst_case_robustness=worst_case,
                mean_robustness=mean_robustness,
                convergence_delta=convergence_delta,
            )
            
            # Check convergence
            if convergence_delta < self._config.convergence_threshold:
                converged = True
                self.logger.info(
                    f"Adaptive evaluation converged at iteration {iteration}",
                    final_worst_case=worst_case,
                )
                break
            
            # Check compute budget
            if total_compute_time > self._config.compute_budget_minutes * 60:
                self.logger.warning(
                    "Compute budget exceeded",
                    total_time=total_compute_time,
                    budget_minutes=self._config.compute_budget_minutes,
                )
                break
        
        self._completed_at = datetime.utcnow()
        
        # Build final result
        final_vulns = self._vulnerability_analyzer.compute_vulnerabilities()
        
        result = AdaptiveEvaluationResult(
            config=self._config,
            total_iterations=len(self._iteration_results),
            converged=converged,
            final_worst_case_robustness=self._current_worst_case,
            initial_worst_case_robustness=self._initial_worst_case,
            robustness_improvement=self._initial_worst_case - self._current_worst_case,
            iteration_results=self._iteration_results,
            final_vulnerabilities=final_vulns,
            total_compute_time_seconds=total_compute_time,
            total_samples_evaluated=total_samples,
            config_hash=self._strategy_evolution.config_hash,
            started_at=self._started_at,
            completed_at=self._completed_at,
        )
        
        self.logger.info(
            "Adaptive evaluation completed",
            total_iterations=result.total_iterations,
            converged=converged,
            final_worst_case=result.final_worst_case_robustness,
        )
        
        return result
    
    async def _run_initial_baseline(
        self,
        evaluation_fn,
        attack_types: List[str],
    ) -> Dict[str, Any]:
        """
        Run initial baseline evaluation.
        
        Args:
            evaluation_fn: Evaluation function
            attack_types: Attack types to evaluate
            
        Returns:
            Dictionary with baseline metrics
        """
        # Use uniform probability for baseline
        uniform_probs = {at: 1.0 / len(attack_types) for at in attack_types}
        
        # Run evaluation
        return await self._run_iteration_evaluation(
            evaluation_fn,
            None,  # Use uniform
        )
    
    async def _run_iteration_evaluation(
        self,
        evaluation_fn,
        selection_probs,
    ) -> Dict[str, Any]:
        """
        Run a single iteration of evaluation.
        
        Args:
            evaluation_fn: Function to run evaluation
            selection_probs: Selection probabilities
            
        Returns:
            Dictionary with iteration metrics
        """
        # This is a placeholder - in real implementation, this would:
        # 1. Select attacks based on probabilities
        # 2. Run the evaluation function
        # 3. Collect results
        
        # For now, return placeholder metrics
        # In production, this would call the actual evaluation
        
        results = {
            "worst_case_robustness": 0.5,
            "mean_robustness": 0.5,
            "samples_evaluated": 0,
        }
        
        return results
    
    def add_evaluation_result(
        self,
        attack_type: str,
        baseline_metrics: Dict[str, float],
        adversarial_metrics: Dict[str, float],
        model_name: str = "unknown",
        dataset_name: str = "unknown",
    ) -> None:
        """
        Add an evaluation result to the feedback loop.
        
        Args:
            attack_type: Type of attack evaluated
            baseline_metrics: Metrics from baseline evaluation
            adversarial_metrics: Metrics from adversarial evaluation
            model_name: Name of model evaluated
            dataset_name: Name of dataset used
        """
        # Add to vulnerability analyzer
        self._vulnerability_analyzer.add_evaluation_result(
            attack_type=attack_type,
            baseline_metrics=baseline_metrics,
            adversarial_metrics=adversarial_metrics,
        )
        
        # Add to strategy evolution
        self._strategy_evolution.add_evaluation(
            attack_type=attack_type,
            baseline_metrics=baseline_metrics,
            adversarial_metrics=adversarial_metrics,
            model_name=model_name,
            dataset_name=dataset_name,
        )
        
        self.logger.debug(
            "Added evaluation result to feedback loop",
            attack_type=attack_type,
        )
    
    def _create_default_result(
        self,
        error: Optional[str] = None,
    ) -> AdaptiveEvaluationResult:
        """Create a default result when adaptive mode is disabled."""
        return AdaptiveEvaluationResult(
            config=self._config,
            total_iterations=0,
            converged=False,
            final_worst_case_robustness=0.5,
            initial_worst_case_robustness=0.5,
            robustness_improvement=0.0,
            iteration_results=[],
            final_vulnerabilities={},
            total_compute_time_seconds=0.0,
            total_samples_evaluated=0,
            config_hash=self._strategy_evolution.config_hash,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
    
    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current state of the feedback engine.
        
        Returns:
            Dictionary with current state
        """
        return {
            "config": self._config.model_dump(),
            "iterations_completed": len(self._iteration_results),
            "current_worst_case": self._current_worst_case,
            "initial_worst_case": self._initial_worst_case,
            "vulnerability_analyzer_stats": self._vulnerability_analyzer.get_statistics(),
            "strategy_evolution_stats": self._strategy_evolution.get_statistics(),
        }


# Global feedback engine instance
_feedback_engine: Optional[FeedbackEngine] = None


def get_feedback_engine(
    config: Optional[AdaptiveConfig] = None,
) -> FeedbackEngine:
    """
    Get the global feedback engine instance.
    
    Args:
        config: Optional adaptive configuration
        
    Returns:
        FeedbackEngine singleton
    """
    global _feedback_engine
    if _feedback_engine is None:
        _feedback_engine = FeedbackEngine(config=config)
    return _feedback_engine


def reset_feedback_engine() -> None:
    """Reset the global feedback engine."""
    global _feedback_engine
    _feedback_engine = None


__all__ = [
    "FeedbackEngine",
    "get_feedback_engine",
    "reset_feedback_engine",
]
