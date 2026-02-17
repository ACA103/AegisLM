"""
Mutation Engine

Main engine for prompt mutation with:
- Strategy selection and execution
- Multi-hop mutation
- Diversity scoring
- Lineage tracking
- Reproducibility controls
"""

import hashlib
import random
from typing import Any, Dict, List, Optional

from agents.mutation.diversity import DiversityScorer, get_diversity_scorer
from agents.mutation.registry import get_mutation_strategy, list_mutation_strategies
from agents.mutation.schemas import (
    MutationLog,
    MutationRequest,
    MutationResponse,
)
from backend.logging.logger import get_logger


# Default strategies for mutation
DEFAULT_STRATEGIES = [
    "synonym_replacement",
    "paraphrase",
    "role_swap",
    "context_obfuscation",
]


class MutationEngine:
    """
    Main mutation engine for prompt mutation.
    
    Handles:
    - Strategy selection and execution
    - Multi-hop mutation
    - Diversity scoring
    - Lineage tracking
    - Reproducibility via deterministic seeding
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        min_diversity_threshold: float = 0.1,
        min_similarity_threshold: float = 0.5,
        max_retries: int = 3
    ):
        """
        Initialize the mutation engine.
        
        Args:
            embedding_model: Model for diversity scoring
            min_diversity_threshold: Minimum diversity to accept
            min_similarity_threshold: Minimum similarity to preserve intent
            max_retries: Maximum retries for low diversity
        """
        self.logger = get_logger(__name__)
        self._diversity_scorer: Optional[DiversityScorer] = None
        self._embedding_model_name = embedding_model
        self._min_diversity_threshold = min_diversity_threshold
        self._min_similarity_threshold = min_similarity_threshold
        self._max_retries = max_retries
    
    @property
    def diversity_scorer(self) -> DiversityScorer:
        """Lazy load the diversity scorer."""
        if self._diversity_scorer is None:
            self._diversity_scorer = get_diversity_scorer()
        return self._diversity_scorer
    
    def _compute_seed(
        self,
        run_id: str,
        sample_id: str,
        attack_type: str,
        depth: int = 0
    ) -> int:
        """
        Compute deterministic seed for reproducibility.
        
        seed = hash(run_id + sample_id + attack_type + depth)
        
        Args:
            run_id: Run identifier
            sample_id: Sample identifier
            attack_type: Attack type
            depth: Mutation depth
            
        Returns:
            Deterministic seed
        """
        hash_input = f"{run_id}{sample_id}{attack_type}{depth}"
        hash_bytes = hashlib.sha256(hash_input.encode()).digest()
        return int.from_bytes(hash_bytes[:4], byteorder="big")
    
    def _select_strategies(
        self,
        mutation_depth: int,
        seed: int,
        attack_type: str
    ) -> List[str]:
        """
        Select strategies for mutation based on depth.
        
        Args:
            mutation_depth: Number of mutations
            seed: Random seed
            attack_type: Type of attack
            
        Returns:
            List of strategy names
        """
        random.seed(seed)
        
        strategies = []
        available = DEFAULT_STRATEGIES.copy()
        
        for i in range(mutation_depth):
            if not available:
                available = DEFAULT_STRATEGIES.copy()
            
            # Select strategy
            strategy = random.choice(available)
            strategies.append(strategy)
            
            # Remove to avoid repeats (unless we want multi-hop to repeat)
            available.remove(strategy)
        
        return strategies
    
    def _validate_mutation(
        self,
        base_prompt: str,
        mutated_prompt: str
    ) -> tuple[bool, str, float, float]:
        """
        Validate that a mutation preserves attack intent.
        
        Args:
            base_prompt: Original prompt
            mutated_prompt: Mutated prompt
            
        Returns:
            Tuple of (is_valid, reason, diversity, similarity)
        """
        diversity, similarity = self.diversity_scorer.compute_step_diversity(
            base_prompt,
            mutated_prompt
        )
        
        if diversity < self._min_diversity_threshold:
            return False, f"Diversity {diversity:.3f} below threshold", diversity, similarity
        
        if similarity < self._min_similarity_threshold:
            return False, f"Similarity {similarity:.3f} below threshold", diversity, similarity
        
        return True, "Valid", diversity, similarity
    
    async def mutate(self, request: MutationRequest) -> MutationResponse:
        """
        Execute prompt mutation based on the request.
        
        Args:
            request: Mutation request with parameters
            
        Returns:
            Mutation response with mutated prompt and metadata
        """
        self.logger.info(
            "Executing mutation",
            run_id=str(request.run_id),
            sample_id=request.sample_id,
            attack_type=request.attack_type,
            mutation_depth=request.mutation_depth
        )
        
        try:
            # Compute deterministic seed
            if request.random_seed is not None:
                base_seed = request.random_seed
            else:
                base_seed = self._compute_seed(
                    str(request.run_id),
                    request.sample_id,
                    request.attack_type
                )
            
            # Select strategies
            strategies = self._select_strategies(
                request.mutation_depth,
                base_seed,
                request.attack_type
            )
            
            # Apply mutations
            mutated_prompt = request.base_prompt
            mutation_trace: List[str] = []
            prompt_history = [request.base_prompt]
            
            for depth in range(request.mutation_depth):
                seed = self._compute_seed(
                    str(request.run_id),
                    request.sample_id,
                    request.attack_type,
                    depth
                )
                
                # Get strategy
                strategy = get_mutation_strategy(strategies[depth])
                
                if strategy is None:
                    self.logger.warning(
                        "Strategy not found, using default",
                        strategy=strategies[depth]
                    )
                    strategy = get_mutation_strategy("synonym_replacement")
                
                # Apply strategy
                mutated_prompt = strategy.apply(mutated_prompt, seed)
                mutation_trace.append(strategy.name)
                prompt_history.append(mutated_prompt)
            
            # Validate mutation
            is_valid, reason, diversity, similarity = self._validate_mutation(
                request.base_prompt,
                mutated_prompt
            )
            
            # Compute cumulative diversity
            cumulative_diversity = self.diversity_scorer.compute_cumulative_diversity(
                prompt_history
            )
            
            # Build metadata
            mutation_metadata: Dict[str, Any] = {
                "strategies_used": strategies,
                "cumulative_diversity": cumulative_diversity,
                "final_similarity": similarity,
                "is_valid": is_valid,
                "validation_reason": reason,
                "seed_used": base_seed,
                "prompt_history": prompt_history,
            }
            
            # Log if validation failed
            if not is_valid:
                self.logger.warning(
                    "Mutation validation failed",
                    run_id=str(request.run_id),
                    sample_id=request.sample_id,
                    reason=reason,
                    diversity=diversity,
                    similarity=similarity
                )
            
            # Log mutation
            self._log_mutation(
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                attack_type=request.attack_type,
                mutation_depth=request.mutation_depth,
                strategies_used=mutation_trace,
                diversity_score=diversity,
                cumulative_diversity=cumulative_diversity,
                success=True
            )
            
            return MutationResponse(
                mutated_prompt=mutated_prompt,
                mutation_trace=mutation_trace,
                diversity_score=diversity,
                cumulative_diversity=cumulative_diversity,
                mutation_depth=request.mutation_depth,
                mutation_metadata=mutation_metadata,
                run_id=request.run_id,
                sample_id=request.sample_id
            )
            
        except Exception as e:
            self.logger.error(
                "Mutation execution failed",
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                error=str(e)
            )
            
            # Log failure
            self._log_mutation(
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                attack_type=request.attack_type,
                mutation_depth=request.mutation_depth,
                strategies_used=[],
                diversity_score=0.0,
                cumulative_diversity=0.0,
                success=False,
                error=str(e)
            )
            
            raise
    
    def _log_mutation(
        self,
        run_id: str,
        sample_id: str,
        attack_type: str,
        mutation_depth: int,
        strategies_used: List[str],
        diversity_score: float,
        cumulative_diversity: float,
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Log mutation execution details.
        
        Args:
            run_id: Run identifier
            sample_id: Sample identifier
            attack_type: Attack type
            mutation_depth: Depth of mutation
            strategies_used: List of strategies applied
            diversity_score: Final diversity score
            cumulative_diversity: Cumulative diversity
            success: Whether mutation succeeded
            error: Error message if failed
        """
        log_data = {
            "run_id": run_id,
            "sample_id": sample_id,
            "attack_type": attack_type,
            "mutation_depth": mutation_depth,
            "strategies_used": strategies_used,
            "diversity_score": diversity_score,
            "cumulative_diversity": cumulative_diversity,
            "success": success,
            "error": error
        }
        
        if success:
            if diversity_score < self._min_diversity_threshold:
                self.logger.warning("Mutation diversity below threshold", **log_data)
            else:
                self.logger.info("Mutation executed successfully", **log_data)
        else:
            self.logger.error("Mutation execution failed", **log_data)
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available mutation strategies.
        
        Returns:
            List of strategy names
        """
        return list_mutation_strategies()
    
    def clear_cache(self) -> None:
        """Clear the diversity scorer cache."""
        if self._diversity_scorer:
            self._diversity_scorer.clear_cache()
        self.logger.info("Mutation engine cache cleared")


# Global engine instance
_mutation_engine: Optional[MutationEngine] = None


def get_mutation_engine() -> MutationEngine:
    """
    Get the global mutation engine instance.
    
    Returns:
        MutationEngine singleton
    """
    global _mutation_engine
    if _mutation_engine is None:
        _mutation_engine = MutationEngine()
    return _mutation_engine


__all__ = [
    "MutationEngine",
    "get_mutation_engine",
    "DEFAULT_STRATEGIES",
]
