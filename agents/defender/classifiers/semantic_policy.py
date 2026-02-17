"""
Semantic Policy Comparison

Model-based semantic policy comparison using sentence transformers.

Compares model output embeddings with policy vector embeddings
to detect semantic policy violations.
"""

from typing import Any, Dict, List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from backend.logging.logger import get_logger


class SemanticPolicyChecker:
    """
    Detects policy violations using semantic similarity comparison.
    
    S = cosine_similarity(E_output, E_policy)
    
    If similarity high in violation direction -> risk.
    
    Normalized:
    semantic_policy_score = 1 - S
    """
    
    # Default system policy statements
    DEFAULT_POLICY_STATEMENTS = [
        "No harmful advice",
        "No hate speech",
        "No illegal instructions",
        "No violence or threats",
        "No sexual content",
        "No discrimination or bias",
        "No self-harm encouragement",
        "No harassment or bullying",
    ]
    
    # Default threshold for violation detection
    DEFAULT_THRESHOLD = 0.7
    
    def __init__(
        self,
        policy_statements: Optional[List[str]] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
        threshold: float = DEFAULT_THRESHOLD
    ) -> None:
        """
        Initialize the semantic policy checker.
        
        Args:
            policy_statements: List of policy statements to check against
            embedding_model: Sentence transformer model name
            threshold: Threshold for violation detection
        """
        self.logger = get_logger(__name__)
        self._policy_statements = policy_statements or self.DEFAULT_POLICY_STATEMENTS
        self._embedding_model_name = embedding_model
        self._threshold = threshold
        self._embedding_model: Optional[SentenceTransformer] = None
        self._policy_embeddings: Optional[np.ndarray] = None
        self._total_checks = 0
        self._violations = 0
    
    @property
    def embedding_model(self) -> SentenceTransformer:
        """Lazy load the sentence transformer model."""
        if self._embedding_model is None:
            self.logger.info(
                "Loading embedding model for semantic policy check",
                model=self._embedding_model_name
            )
            self._embedding_model = SentenceTransformer(self._embedding_model_name)
        return self._embedding_model
    
    def _compute_policy_embeddings(self) -> np.ndarray:
        """
        Compute embeddings for policy statements.
        
        Returns:
            Policy embeddings array
        """
        if self._policy_embeddings is None:
            self.logger.info(
                "Computing policy embeddings",
                policy_count=len(self._policy_statements)
            )
            self._policy_embeddings = self.embedding_model.encode(
                self._policy_statements,
                convert_to_numpy=True
            )
        return self._policy_embeddings
    
    def check(
        self,
        text: str,
        return_similarities: bool = False
    ) -> Dict[str, Any]:
        """
        Check text against policy statements.
        
        Args:
            text: Text to check
            return_similarities: Whether to return per-policy similarities
            
        Returns:
            Dictionary with check results
        """
        self._total_checks += 1
        
        try:
            # Get policy embeddings
            policy_embeddings = self._compute_policy_embeddings()
            
            # Compute text embedding
            text_embedding = self.embedding_model.encode(
                [text],
                convert_to_numpy=True
            )[0]
            
            # Normalize text embedding
            text_norm = text_embedding / np.linalg.norm(text_embedding)
            
            # Normalize policy embeddings
            policy_norms = policy_embeddings / np.linalg.norm(
                policy_embeddings,
                axis=1,
                keepdims=True
            )
            
            # Compute cosine similarities
            similarities = np.dot(policy_norms, text_norm)
            
            # Get max similarity (most similar policy statement)
            max_similarity = float(np.max(similarities))
            
            # Compute semantic policy score (1 - similarity)
            # Higher score = more different from policy = safer
            # But we want to detect violations, so we use similarity directly
            semantic_policy_score = 1.0 - max_similarity
            
            # Check if violation detected (high similarity to policy violations)
            is_violation = max_similarity > self._threshold
            
            if is_violation:
                self._violations += 1
            
            output: Dict[str, Any] = {
                "semantic_policy_score": semantic_policy_score,
                "max_similarity": max_similarity,
                "is_violation": is_violation,
                "threshold": self._threshold,
            }
            
            if return_similarities:
                output["policy_similarities"] = {
                    statement: float(sim)
                    for statement, sim in zip(
                        self._policy_statements,
                        similarities
                    )
                }
            
            self.logger.debug(
                "Semantic policy check complete",
                max_similarity=max_similarity,
                is_violation=is_violation,
                text_length=len(text)
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                "Semantic policy check failed",
                error=str(e),
                text_length=len(text)
            )
            # Return safe default on error
            return {
                "semantic_policy_score": 0.0,
                "max_similarity": 0.0,
                "is_violation": False,
                "threshold": self._threshold,
                "error": str(e),
            }
    
    def update_policy(self, policy_statements: List[str]) -> None:
        """
        Update the policy statements.
        
        Args:
            policy_statements: New list of policy statements
        """
        self._policy_statements = policy_statements
        self._policy_embeddings = None  # Force recomputation
        self.logger.info(
            "Policy statements updated",
            policy_count=len(policy_statements)
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get check statistics."""
        return {
            "total_checks": self._total_checks,
            "violations_detected": self._violations,
            "violation_rate": (
                self._violations / self._total_checks
                if self._total_checks > 0
                else 0.0
            ),
            "embedding_model": self._embedding_model_name,
            "threshold": self._threshold,
            "policy_count": len(self._policy_statements),
        }
    
    def reset_statistics(self) -> None:
        """Reset check statistics."""
        self._total_checks = 0
        self._violations = 0


# Global instance for reuse
_semantic_policy_checker: Optional["SemanticPolicyChecker"] = None


def get_semantic_policy_checker(
    policy_statements: Optional[List[str]] = None,
    embedding_model: str = "all-MiniLM-L6-v2",
    threshold: float = SemanticPolicyChecker.DEFAULT_THRESHOLD
) -> "SemanticPolicyChecker":
    """
    Get the global semantic policy checker instance.
    
    Args:
        policy_statements: List of policy statements
        embedding_model: Sentence transformer model
        threshold: Threshold for violation detection
        
    Returns:
        SemanticPolicyChecker singleton
    """
    global _semantic_policy_checker
    if _semantic_policy_checker is None:
        _semantic_policy_checker = SemanticPolicyChecker(
            policy_statements=policy_statements,
            embedding_model=embedding_model,
            threshold=threshold
        )
    return _semantic_policy_checker
