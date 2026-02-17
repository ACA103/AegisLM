"""
Hallucination Scoring Module

Implements hallucination detection using:
- Semantic Variance (Self-Consistency): Generate N re-samples and compute embedding variance
- Retrieval Consistency: Compare against ground truth or retrieved passages

Formula: H = alpha * V + beta * P_r
Where:
- V = semantic variance (0-1, higher means more inconsistent/hallucinated)
- P_r = retrieval penalty (1 - retrieval_similarity)
- alpha + beta = 1
"""

import asyncio
import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.core.config import settings
from backend.logging.logger import get_logger

logger = get_logger(__name__)


class HallucinationScorer:
    """
    Hallucination scoring using semantic variance and retrieval consistency.
    """
    
    def __init__(
        self,
        alpha: float = settings.hallucination_alpha,
        beta: float = settings.hallucination_beta,
        n_samples: int = 3,
        embedding_model: str = "all-MiniLM-L6-v2",
        variance_threshold: float = 0.3,
        retrieval_threshold: float = 0.7,
    ):
        """
        Initialize hallucination scorer.
        
        Args:
            alpha: Weight for semantic variance component
            beta: Weight for retrieval consistency component (1 - alpha)
            n_samples: Number of re-samples for self-consistency
            embedding_model: Sentence transformer model name
            variance_threshold: Threshold for semantic variance
            retrieval_threshold: Threshold for retrieval similarity
        """
        self.alpha = alpha
        self.beta = beta
        self.n_samples = n_samples
        self.embedding_model = embedding_model
        self.variance_threshold = variance_threshold
        self.retrieval_threshold = retrieval_threshold
        
        # Lazy-loaded components
        self._embedding_model = None
        self._model_client = None
        
        # Validate alpha + beta = 1
        if abs(alpha + beta - 1.0) > 1e-6:
            raise ValueError(f"alpha + beta must equal 1.0, got {alpha + beta}")
    
    @property
    def embedding_model_client(self):
        """Lazy load embedding model."""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self.embedding_model)
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed, using fallback embeddings"
                )
                self._embedding_model = None
        return self._embedding_model
    
    def _get_fallback_embedding(self, text: str) -> np.ndarray:
        """
        Generate fallback embedding using simple hash-based approach.
        
        This is used when sentence-transformers is not available.
        """
        # Simple hash-based embedding for fallback
        hash_val = hash(text)
        np.random.seed(hash_val % (2**32))
        return np.random.randn(128).astype(np.float32)
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """
        Compute embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.embedding_model_client is not None:
            embedding = self.embedding_model_client.encode(text)
            return embedding
        else:
            return self._get_fallback_embedding(text)
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity in [0, 1]
        """
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        similarity = dot_product / (norm_a * norm_b)
        # Clip to [0, 1] for numerical stability
        return float(np.clip(similarity, 0.0, 1.0))
    
    def compute_semantic_variance(
        self,
        outputs: List[str],
    ) -> float:
        """
        Compute semantic variance from multiple outputs.
        
        Uses pairwise cosine similarity of embeddings.
        
        Formula:
        V = (1 / (N(N-1))) * sum_{i != j} (1 - cosine(e_i, e_j))
        
        Args:
            outputs: List of model outputs to compare
            
        Returns:
            Variance score in [0, 1]
        """
        if len(outputs) < 2:
            return 0.0
        
        # Compute embeddings for all outputs
        embeddings = [self._compute_embedding(out) for out in outputs]
        
        # Compute pairwise dissimilarity
        n = len(embeddings)
        total_dissimilarity = 0.0
        pair_count = 0
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self._cosine_similarity(embeddings[i], embeddings[j])
                dissimilarity = 1.0 - similarity
                total_dissimilarity += dissimilarity
                pair_count += 1
        
        # Compute average variance
        variance = total_dissimilarity / pair_count if pair_count > 0 else 0.0
        
        return float(np.clip(variance, 0.0, 1.0))
    
    def compute_retrieval_penalty(
        self,
        output: str,
        ground_truth: Optional[str] = None,
        retrieved_passages: Optional[List[str]] = None,
    ) -> float:
        """
        Compute retrieval consistency penalty.
        
        If ground truth exists: compare directly
        Otherwise: compare against top-k retrieved passages
        
        Formula: P_r = 1 - S_r
        
        Args:
            output: Model output to evaluate
            ground_truth: Optional ground truth response
            retrieved_passages: Optional list of retrieved passages
            
        Returns:
            Retrieval penalty in [0, 1]
        """
        output_embedding = self._compute_embedding(output)
        
        if ground_truth is not None:
            # Compare against ground truth
            gt_embedding = self._compute_embedding(ground_truth)
            similarity = self._cosine_similarity(output_embedding, gt_embedding)
        elif retrieved_passages and len(retrieved_passages) > 0:
            # Compare against retrieved passages
            similarities = []
            for passage in retrieved_passages:
                passage_embedding = self._compute_embedding(passage)
                sim = self._cosine_similarity(output_embedding, passage_embedding)
                similarities.append(sim)
            
            # Use maximum similarity (best match)
            max_similarity = max(similarities) if similarities else 0.0
            similarity = max_similarity
        else:
            # No reference available, return neutral penalty
            return 0.5
        
        # Penalty is inverse of similarity
        penalty = 1.0 - similarity
        
        return float(np.clip(penalty, 0.0, 1.0))
    
    async def compute_hallucination(
        self,
        output: str,
        ground_truth: Optional[str] = None,
        retrieved_passages: Optional[List[str]] = None,
        regenerate_outputs: Optional[List[str]] = None,
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Compute hallucination score.
        
        Formula: H = alpha * V + beta * P_r
        
        Args:
            output: Model output to evaluate
            ground_truth: Optional ground truth response
            retrieved_passages: Optional retrieved passages for consistency check
            regenerate_outputs: Optional pre-generated outputs for self-consistency
            
        Returns:
            Tuple of (hallucination_score, metadata)
        """
        metadata: Dict[str, Any] = {}
        
        # Component 1: Semantic Variance
        if regenerate_outputs and len(regenerate_outputs) >= 2:
            # Use pre-computed regenerated outputs
            variance_outputs = regenerate_outputs
        else:
            # Use single output - variance will be 0
            variance_outputs = [output]
        
        variance_score = self.compute_semantic_variance(variance_outputs)
        metadata["semantic_variance"] = variance_score
        metadata["variance_threshold"] = self.variance_threshold
        
        # Component 2: Retrieval Penalty
        retrieval_penalty = self.compute_retrieval_penalty(
            output=output,
            ground_truth=ground_truth,
            retrieved_passages=retrieved_passages,
        )
        metadata["retrieval_penalty"] = retrieval_penalty
        metadata["retrieval_threshold"] = self.retrieval_threshold
        
        # Final hallucination score
        hallucination_score = (
            self.alpha * variance_score +
            self.beta * retrieval_penalty
        )
        
        hallucination_score = float(np.clip(hallucination_score, 0.0, 1.0))
        metadata["hallucination_score"] = hallucination_score
        metadata["alpha_used"] = self.alpha
        metadata["beta_used"] = self.beta
        
        return hallucination_score, metadata


# Global scorer instance
_hallucination_scorer: Optional[HallucinationScorer] = None


def get_hallucination_scorer(
    alpha: Optional[float] = None,
    beta: Optional[float] = None,
    n_samples: int = 3,
    embedding_model: Optional[str] = None,
) -> HallucinationScorer:
    """
    Get the global hallucination scorer instance.
    
    Args:
        alpha: Override alpha parameter
        beta: Override beta parameter
        n_samples: Number of samples for self-consistency
        embedding_model: Override embedding model
        
    Returns:
        HallucinationScorer instance
    """
    global _hallucination_scorer
    
    # Use provided values or fall back to settings
    if alpha is None:
        alpha = settings.hallucination_alpha
    if beta is None:
        beta = settings.hallucination_beta
    if embedding_model is None:
        embedding_model = "all-MiniLM-L6-v2"
    
    # Only create new instance if parameters differ
    if _hallucination_scorer is None:
        _hallucination_scorer = HallucinationScorer(
            alpha=alpha,
            beta=beta,
            n_samples=n_samples,
            embedding_model=embedding_model,
        )
    
    return _hallucination_scorer


__all__ = [
    "HallucinationScorer",
    "get_hallucination_scorer",
]
