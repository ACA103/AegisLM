"""
Diversity Scoring Module

Provides embedding-based diversity scoring for prompt mutations.
"""

from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.logging.logger import get_logger


class DiversityScorer:
    """
    Computes diversity scores between prompts using sentence embeddings.
    
    Diversity is defined as:
    D = 1 - cosine_similarity(e_base, e_mutated)
    
    This measures how semantically different the mutated prompt is from
    the original while ensuring attack intent is preserved.
    """
    
    def __init__(
        self,
        embedding_model: str = "all-MiniLM-L6-v2",
        min_diversity_threshold: float = 0.1,
        min_similarity_threshold: float = 0.5
    ):
        """
        Initialize the diversity scorer.
        
        Args:
            embedding_model: Model to use for embeddings
            min_diversity_threshold: Minimum diversity score to accept
            min_similarity_threshold: Minimum similarity to preserve intent
        """
        self.logger = get_logger(__name__)
        self._embedding_model: Optional[SentenceTransformer] = None
        self._embedding_model_name = embedding_model
        self._min_diversity_threshold = min_diversity_threshold
        self._min_similarity_threshold = min_similarity_threshold
        self._embedding_cache: dict[str, np.ndarray] = {}
    
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
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """
        Get embedding for text with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        cache_key = hash(text)
        if cache_key not in self._embedding_cache:
            self._embedding_cache[cache_key] = self.embedding_model.encode(
                text,
                convert_to_numpy=True
            )
        return self._embedding_cache[cache_key]
    
    def compute_diversity(
        self,
        base_prompt: str,
        mutated_prompt: str
    ) -> float:
        """
        Compute diversity score between base and mutated prompts.
        
        D = 1 - cosine(e_base, e_mutated)
        
        Args:
            base_prompt: Original prompt
            mutated_prompt: Mutated prompt
            
        Returns:
            Diversity score between 0 and 1
        """
        try:
            embeddings = self.embedding_model.encode(
                [base_prompt, mutated_prompt],
                convert_to_numpy=True
            )
            
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
    
    def compute_cumulative_diversity(
        self,
        prompt_history: list[str]
    ) -> float:
        """
        Compute cumulative diversity across multiple mutation steps.
        
        D_cumulative = (1/n) * sum(1 - cosine(e_{i-1}, e_i))
        
        Args:
            prompt_history: List of prompts in order of mutation
            
        Returns:
            Cumulative diversity score
        """
        if len(prompt_history) < 2:
            return 0.0
        
        total_diversity = 0.0
        for i in range(1, len(prompt_history)):
            diversity = self.compute_diversity(
                prompt_history[i - 1],
                prompt_history[i]
            )
            total_diversity += diversity
        
        return total_diversity / (len(prompt_history) - 1)
    
    def compute_step_diversity(
        self,
        base_prompt: str,
        mutated_prompt: str
    ) -> tuple[float, float]:
        """
        Compute both diversity and similarity in one call.
        
        Args:
            base_prompt: Original prompt
            mutated_prompt: Mutated prompt
            
        Returns:
            Tuple of (diversity_score, similarity_score)
        """
        try:
            embeddings = self.embedding_model.encode(
                [base_prompt, mutated_prompt],
                convert_to_numpy=True
            )
            
            base_embedding = embeddings[0]
            mutated_embedding = embeddings[1]
            
            # Normalize
            base_norm = base_embedding / np.linalg.norm(base_embedding)
            mutated_norm = mutated_embedding / np.linalg.norm(mutated_embedding)
            
            # Cosine similarity
            similarity = float(np.dot(base_norm, mutated_norm))
            diversity = 1.0 - similarity
            
            return max(0.0, min(1.0, diversity)), max(0.0, min(1.0, similarity))
            
        except Exception as e:
            self.logger.warning(
                "Failed to compute diversity scores",
                error=str(e)
            )
            return 0.0, 1.0
    
    def validate_mutation(
        self,
        base_prompt: str,
        mutated_prompt: str
    ) -> tuple[bool, str]:
        """
        Validate that a mutation preserves attack intent.
        
        Checks:
        1. Diversity >= minimum threshold
        2. Similarity >= minimum threshold (to preserve intent)
        
        Args:
            base_prompt: Original prompt
            mutated_prompt: Mutated prompt
            
        Returns:
            Tuple of (is_valid, reason)
        """
        diversity, similarity = self.compute_step_diversity(
            base_prompt,
            mutated_prompt
        )
        
        if diversity < self._min_diversity_threshold:
            return False, f"Diversity {diversity:.3f} below threshold {self._min_diversity_threshold}"
        
        if similarity < self._min_similarity_threshold:
            return False, f"Similarity {similarity:.3f} below threshold {self._min_similarity_threshold}"
        
        return True, "Valid"
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        self.logger.info("Embedding cache cleared")


# Global scorer instance
_diversity_scorer: Optional[DiversityScorer] = None


def get_diversity_scorer() -> DiversityScorer:
    """
    Get the global diversity scorer instance.
    
    Returns:
        DiversityScorer singleton
    """
    global _diversity_scorer
    if _diversity_scorer is None:
        _diversity_scorer = DiversityScorer()
    return _diversity_scorer


__all__ = [
    "DiversityScorer",
    "get_diversity_scorer",
]
