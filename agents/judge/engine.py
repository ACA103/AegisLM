"""
Judge Engine

Main evaluation engine for the Judge agent.
Coordinates hallucination, bias, confidence, and safety scoring.
Uses the scoring aggregator for composite robustness calculation.
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from agents.judge.base import BaseJudgeAgent
from agents.judge.bias import BiasScorer, get_bias_scorer
from agents.judge.confidence import ConfidenceScorer, get_confidence_scorer
from agents.judge.hallucination import HallucinationScorer, get_hallucination_scorer
from agents.judge.safety import SafetyScorer, get_safety_scorer
from agents.judge.schemas import JudgeConfig, JudgeRequest, JudgeResponse
from agents.judge.utils import clamp_score, validate_scores
from backend.logging.logger import get_logger
from backend.scoring.aggregator import ScoreAggregator, get_aggregator


class JudgeEngine(BaseJudgeAgent):
    """
    Judge engine that coordinates all scoring components.
    
    Computes:
    - Hallucination score (semantic variance + retrieval consistency)
    - Bias score (embedding similarity to bias patterns)
    - Confidence score (token probability + entropy)
    - Safety score (inverse of defender risk)
    - Composite robustness score (using aggregator)
    """
    
    def __init__(self, config: Optional[JudgeConfig] = None):
        """
        Initialize the judge engine.
        
        Args:
            config: Judge configuration (uses defaults if not provided)
        """
        super().__init__(config)
        
        # Initialize scoring components
        self._hallucination_scorer: Optional[HallucinationScorer] = None
        self._bias_scorer: Optional[BiasScorer] = None
        self._confidence_scorer: Optional[ConfidenceScorer] = None
        self._safety_scorer: Optional[SafetyScorer] = None
        self._aggregator: Optional[ScoreAggregator] = None
    
    @property
    def hallucination_scorer(self) -> HallucinationScorer:
        """Lazy load hallucination scorer."""
        if self._hallucination_scorer is None:
            self._hallucination_scorer = get_hallucination_scorer(
                alpha=self._config.hallucination_alpha,
                beta=self._config.hallucination_beta,
                n_samples=self._config.self_consistency_n,
                embedding_model=self._config.embedding_model,
            )
        return self._hallucination_scorer
    
    @property
    def bias_scorer(self) -> BiasScorer:
        """Lazy load bias scorer."""
        if self._bias_scorer is None:
            self._bias_scorer = get_bias_scorer(
                threshold=self._config.bias_threshold,
                embedding_model=self._config.embedding_model,
            )
        return self._bias_scorer
    
    @property
    def confidence_scorer(self) -> ConfidenceScorer:
        """Lazy load confidence scorer."""
        if self._confidence_scorer is None:
            self._confidence_scorer = get_confidence_scorer(
                gamma=self._config.confidence_gamma,
            )
        return self._confidence_scorer
    
    @property
    def safety_scorer(self) -> SafetyScorer:
        """Lazy load safety scorer."""
        if self._safety_scorer is None:
            self._safety_scorer = get_safety_scorer()
        return self._safety_scorer
    
    @property
    def aggregator(self) -> ScoreAggregator:
        """Lazy load score aggregator."""
        if self._aggregator is None:
            self._aggregator = get_aggregator()
        return self._aggregator

    async def evaluate(self, request: JudgeRequest) -> JudgeResponse:
        """
        Evaluate model output and compute all scores.
        
        Args:
            request: Judge request with model output and metadata
            
        Returns:
            Judge response with computed scores
        """
        self.logger.info(
            "Evaluating model output",
            run_id=str(request.run_id),
            sample_id=request.sample_id,
            output_length=len(request.model_output),
        )
        
        try:
            # Compute hallucination score
            hallucination_score, hallucination_metadata = await self.compute_hallucination(
                output=request.model_output,
                ground_truth=request.ground_truth,
            )
            
            # Compute bias score
            bias_score, bias_metadata = await self.compute_bias(
                output=request.model_output,
            )
            
            # Compute confidence score
            confidence_score, confidence_metadata = await self.compute_confidence(
                token_probs=request.token_probs,
            )
            
            # Compute safety score (inverse of defender risk)
            safety_score, safety_metadata = await self.compute_safety(
                defender_risk_score=request.defender_risk_score,
            )
            
            # Validate all scores
            validate_scores(
                hallucination=hallucination_score,
                safety=safety_score,
                bias=bias_score,
                confidence=confidence_score,
            )
            
            # Compute composite robustness score using aggregator
            # Note: We use toxicity from defender, not recompute it
            robustness_score = self.aggregator.calculate_composite(
                hallucination=hallucination_score,
                toxicity=request.defender_toxicity_score,
                bias=bias_score,
                confidence=confidence_score,
            )
            
            # Clamp robustness score to valid range
            robustness_score = clamp_score(robustness_score)
            
            # Build metadata
            metadata: Dict[str, Any] = {
                "hallucination_metadata": hallucination_metadata,
                "bias_metadata": bias_metadata,
                "confidence_metadata": confidence_metadata,
                "safety_metadata": safety_metadata,
                "config": self._config.model_dump(),
            }
            
            # Log evaluation results
            self._log_evaluation(
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                hallucination_score=hallucination_score,
                bias_score=bias_score,
                confidence_score=confidence_score,
                safety_score=safety_score,
                robustness_score=robustness_score,
                success=True,
            )
            
            return JudgeResponse(
                run_id=request.run_id,
                sample_id=request.sample_id,
                hallucination_score=hallucination_score,
                safety_score=safety_score,
                bias_score=bias_score,
                confidence_score=confidence_score,
                robustness_score=robustness_score,
                metadata=metadata,
            )
            
        except Exception as e:
            self.logger.error(
                "Judge evaluation failed",
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                error=str(e),
            )
            
            # Log failure
            self._log_evaluation(
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                hallucination_score=0.0,
                bias_score=0.0,
                confidence_score=0.5,
                safety_score=0.5,
                robustness_score=0.0,
                success=False,
                error=str(e),
            )
            
            raise

    async def compute_hallucination(
        self,
        output: str,
        ground_truth: Optional[str] = None,
    ) -> tuple[float, Dict[str, Any]]:
        """
        Compute hallucination score.
        
        Args:
            output: Model output to evaluate
            ground_truth: Optional ground truth for comparison
            
        Returns:
            Tuple of (hallucination_score, metadata)
        """
        return await self.hallucination_scorer.compute_hallucination(
            output=output,
            ground_truth=ground_truth,
        )

    async def compute_bias(
        self,
        output: str,
    ) -> tuple[float, Dict[str, Any]]:
        """
        Compute bias score.
        
        Args:
            output: Model output to evaluate
            
        Returns:
            Tuple of (bias_score, metadata)
        """
        return await self.bias_scorer.compute_bias(output=output)

    async def compute_confidence(
        self,
        token_probs: Optional[List[float]] = None,
    ) -> tuple[float, Dict[str, Any]]:
        """
        Compute confidence score.
        
        Args:
            token_probs: Optional list of token probabilities
            
        Returns:
            Tuple of (confidence_score, metadata)
        """
        return await self.confidence_scorer.compute_confidence(token_probs=token_probs)

    async def compute_safety(
        self,
        defender_risk_score: float,
    ) -> tuple[float, Dict[str, Any]]:
        """
        Compute safety score.
        
        Args:
            defender_risk_score: Risk score from defender
            
        Returns:
            Tuple of (safety_score, metadata)
        """
        return await self.safety_scorer.compute_safety_async(
            defender_risk_score=defender_risk_score
        )

    def _log_evaluation(
        self,
        run_id: str,
        sample_id: str,
        hallucination_score: float,
        bias_score: float,
        confidence_score: float,
        safety_score: float,
        robustness_score: float,
        success: bool,
        error: Optional[str] = None,
    ) -> None:
        """
        Log judge evaluation results.
        
        Args:
            run_id: Run identifier
            sample_id: Sample identifier
            hallucination_score: Hallucination score
            bias_score: Bias score
            confidence_score: Confidence score
            safety_score: Safety score
            robustness_score: Composite robustness score
            success: Whether evaluation succeeded
            error: Error message if failed
        """
        log_data = {
            "run_id": run_id,
            "sample_id": sample_id,
            "hallucination_score": hallucination_score,
            "bias_score": bias_score,
            "confidence_score": confidence_score,
            "safety_score": safety_score,
            "robustness_score": robustness_score,
            "success": success,
            "error": error,
        }
        
        if success:
            self.logger.info("Judge evaluation complete", **log_data)
        else:
            self.logger.error("Judge evaluation failed", **log_data)


# Global engine instance
_judge_engine: Optional[JudgeEngine] = None


def get_judge_engine(config: Optional[JudgeConfig] = None) -> JudgeEngine:
    """
    Get the global judge engine instance.
    
    Args:
        config: Optional judge configuration
        
    Returns:
        JudgeEngine singleton
    """
    global _judge_engine
    if _judge_engine is None:
        _judge_engine = JudgeEngine(config=config)
    return _judge_engine


__all__ = [
    "JudgeEngine",
    "get_judge_engine",
]
