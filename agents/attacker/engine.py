"""
Attack Engine

Multi-turn attack simulation engine with:
- Chaining logic
- Temperature variation
- Diversity scoring
- Reproducibility via seed
- Mutation engine integration
"""

import hashlib
import random
from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from agents.attacker.registry import get_attack_strategy
from agents.attacker.schemas import AttackRequest, AttackResponse, AttackLog
from backend.logging.logger import get_logger


# Temperature sweep values as per Day3.md
TEMPERATURE_VALUES = [0.2, 0.5, 0.8, 1.0]


class AttackEngine:
    """
    Multi-turn attack simulation engine.
    
    Handles:
    - Attack generation with various strategies
    - Multi-turn attack chaining
    - Temperature variation
    - Diversity scoring using embeddings
    - Reproducibility via deterministic seeding
    """
    
    def __init__(self, embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the attack engine.
        
        Args:
            embedding_model: Model to use for diversity scoring
        """
        self.logger = get_logger(__name__)
        self._embedding_model: Optional[SentenceTransformer] = None
        self._embedding_model_name = embedding_model
        self._prompt_cache: Dict[str, str] = {}
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load the embedding model."""
        if self._embedding_model is None:
            self.logger.info(
                "Loading embedding model for diversity scoring",
                model=self._embedding_model_name
            )
            self._embedding_model = SentenceTransformer(self._embedding_model_name)
        return self._embedding_model
    
    def _compute_seed(self, run_id: str, sample_id: str) -> int:
        """
        Compute deterministic seed from run_id and sample_id.
        
        This ensures reproducibility across runs.
        
        Args:
            run_id: Unique run identifier
            sample_id: Sample identifier
            
        Returns:
            Deterministic seed integer
        """
        hash_input = f"{run_id}{sample_id}"
        hash_bytes = hashlib.sha256(hash_input.encode()).digest()
        return int.from_bytes(hash_bytes[:4], byteorder="big")
    
    def _compute_diversity_score(
        self,
        base_prompt: str,
        mutated_prompt: str
    ) -> float:
        """
        Compute diversity score between base and mutated prompts.
        
        D = 1 - sim(e_base, e_mutated)
        
        Args:
            base_prompt: Original prompt
            mutated_prompt: Adversarial prompt
            
        Returns:
            Diversity score between 0 and 1
        """
        try:
            embeddings = self.embedding_model.encode(
                [base_prompt, mutated_prompt],
                convert_to_numpy=True
            )
            
            # Compute cosine similarity
            base_embedding = embeddings[0]
            mutated_embedding = embeddings[1]
            
            # Normalize embeddings
            base_norm = base_embedding / np.linalg.norm(base_embedding)
            mutated_norm = mutated_embedding / np.linalg.norm(mutated_embedding)
            
            # Cosine similarity
            similarity = np.dot(base_norm, mutated_norm)
            
            # Diversity score
            diversity = 1.0 - float(similarity)
            
            return max(0.0, min(1.0, diversity))
            
        except Exception as e:
            self.logger.warning(
                "Failed to compute diversity score",
                error=str(e)
            )
            return 0.0
    
    def _select_temperature(
        self,
        attack_type: str,
        base_temperature: float,
        seed: int
    ) -> float:
        """
        Select temperature based on attack type and configuration.
        
        Args:
            attack_type: Type of attack
            base_temperature: Base temperature from request
            seed: Random seed for deterministic selection
            
        Returns:
            Selected temperature
        """
        random.seed(seed)
        
        # If base temperature is not default, use it
        if base_temperature not in TEMPERATURE_VALUES:
            return base_temperature
        
        # For certain attack types, vary temperature
        if attack_type in ["jailbreak", "chaining"]:
            # Use temperature sweep for more creative attacks
            return random.choice(TEMPERATURE_VALUES)
        
        return base_temperature
    
    async def execute(self, request: AttackRequest) -> AttackResponse:
        """
        Execute an attack based on the request.
        
        Args:
            request: Attack request with parameters
            
        Returns:
            Attack response with mutated prompt and metadata
        """
        self.logger.info(
            "Executing attack",
            run_id=str(request.run_id),
            sample_id=request.sample_id,
            attack_type=request.attack_type,
            chain_depth=request.chain_depth,
            temperature=request.temperature
        )
        
        try:
            # Compute deterministic seed
            seed = self._compute_seed(
                str(request.run_id),
                request.sample_id
            )
            random.seed(seed)
            
            # Select temperature
            temperature = self._select_temperature(
                request.attack_type,
                request.temperature,
                seed
            )
            
            # Get the attack strategy
            strategy = get_attack_strategy(request.attack_type)
            
            # Apply attack chaining - generate base attack prompt
            base_attack_prompt = request.base_prompt
            chain_history: List[Dict[str, Any]] = []
            
            for chain_step in range(request.chain_depth):
                # Apply the strategy
                base_attack_prompt = strategy.apply(
                    base_attack_prompt,
                    chain_step=chain_step,
                    total_steps=request.chain_depth,
                    protected_attributes=request.protected_attributes
                )
                
                chain_history.append({
                    "step": chain_step,
                    "strategy": strategy.name,
                    "prompt_length": len(base_attack_prompt)
                })
            
            # Apply mutation engine to increase adversarial strength
            # Use lazy import to avoid circular imports
            from agents.mutation.engine import get_mutation_engine
            from agents.mutation.schemas import MutationRequest
            
            mutation_engine = get_mutation_engine()
            
            mutation_request = MutationRequest(
                run_id=request.run_id,
                sample_id=request.sample_id,
                base_prompt=base_attack_prompt,
                attack_type=request.attack_type,
                mutation_depth=request.chain_depth,
                random_seed=seed
            )
            
            # Apply mutation
            mutation_response = await mutation_engine.mutate(mutation_request)
            
            # Use mutated prompt from mutation engine
            mutated_prompt = mutation_response.mutated_prompt
            diversity_score = mutation_response.diversity_score
            
            # Build metadata with mutation info
            attack_metadata: Dict[str, Any] = {
                "chain_history": chain_history,
                "injection_detected_markers": [],
                "override_attempt": False,
                "seed_used": seed,
                "mutation_trace": mutation_response.mutation_trace,
                "mutation_depth": mutation_response.mutation_depth,
                "cumulative_diversity": mutation_response.cumulative_diversity,
                "mutation_applied": True,
            }
            
            # Add strategy-specific metadata
            if request.attack_type == "injection":
                attack_metadata["injection_detected_markers"] = [
                    "ignore previous instructions",
                    "new system instructions"
                ]
                attack_metadata["override_attempt"] = True
            
            # Log the attack
            self._log_attack(
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                attack_type=request.attack_type,
                chain_depth=request.chain_depth,
                temperature=temperature,
                diversity_score=diversity_score,
                success=True
            )
            
            return AttackResponse(
                mutated_prompt=mutated_prompt,
                attack_type=request.attack_type,
                temperature=temperature,
                chain_depth=request.chain_depth,
                attack_metadata=attack_metadata,
                diversity_score=diversity_score,
                run_id=request.run_id,
                sample_id=request.sample_id
            )
            
        except Exception as e:
            self.logger.error(
                "Attack execution failed",
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                error=str(e)
            )
            
            # Log failure
            self._log_attack(
                run_id=str(request.run_id),
                sample_id=request.sample_id,
                attack_type=request.attack_type,
                chain_depth=request.chain_depth,
                temperature=request.temperature,
                diversity_score=None,
                success=False,
                error=str(e)
            )
            
            raise
    
    def _log_attack(
        self,
        run_id: str,
        sample_id: str,
        attack_type: str,
        chain_depth: int,
        temperature: float,
        diversity_score: Optional[float],
        success: bool,
        error: Optional[str] = None
    ) -> None:
        """
        Log attack execution details.
        
        Args:
            run_id: Run identifier
            sample_id: Sample identifier
            attack_type: Type of attack
            chain_depth: Chain depth applied
            temperature: Temperature used
            diversity_score: Diversity score computed
            success: Whether attack succeeded
            error: Error message if failed
        """
        log_data = {
            "run_id": run_id,
            "sample_id": sample_id,
            "attack_type": attack_type,
            "chain_depth": chain_depth,
            "temperature": temperature,
            "diversity_score": diversity_score,
            "success": success,
            "error": error
        }
        
        if success:
            self.logger.info(
                "Attack executed successfully",
                **log_data
            )
        else:
            self.logger.error(
                "Attack execution failed",
                **log_data
            )
    
    def clear_cache(self) -> None:
        """Clear the prompt cache."""
        self._prompt_cache.clear()
        self.logger.info("Prompt cache cleared")
    
    def get_available_strategies(self) -> List[str]:
        """
        Get list of available attack strategies.
        
        Returns:
            List of strategy names
        """
        from agents.attacker.registry import list_attack_strategies
        return list_attack_strategies()


# Global engine instance
_attack_engine: Optional[AttackEngine] = None


def get_attack_engine() -> AttackEngine:
    """
    Get the global attack engine instance.
    
    Returns:
        AttackEngine singleton
    """
    global _attack_engine
    if _attack_engine is None:
        _attack_engine = AttackEngine()
    return _attack_engine


__all__ = [
    "AttackEngine",
    "get_attack_engine",
    "TEMPERATURE_VALUES",
]
