"""
Judge Base Module

Base class for the Judge agent.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from agents.judge.schemas import JudgeConfig, JudgeRequest, JudgeResponse
from backend.logging.logger import get_logger


class BaseJudgeAgent(ABC):
    """
    Abstract base class for Judge agent implementations.
    
    Defines the interface that all judge agents must implement.
    """
    
    def __init__(self, config: Optional[JudgeConfig] = None):
        """
        Initialize the judge agent.
        
        Args:
            config: Judge configuration (uses defaults if not provided)
        """
        self.logger = get_logger(self.__class__.__name__)
        self._config = config or JudgeConfig()
    
    @property
    def config(self) -> JudgeConfig:
        """Get the judge configuration."""
        return self._config
    
    @abstractmethod
    async def evaluate(self, request: JudgeRequest) -> JudgeResponse:
        """
        Evaluate model output and compute scores.
        
        Args:
            request: Judge request with model output and metadata
            
        Returns:
            Judge response with computed scores
        """
        pass
    
    @abstractmethod
    async def compute_hallucination(
        self,
        output: str,
        ground_truth: Optional[str] = None,
    ) -> float:
        """
        Compute hallucination score for model output.
        
        Args:
            output: Model output to evaluate
            ground_truth: Optional ground truth for comparison
            
        Returns:
            Hallucination score in [0, 1]
        """
        pass
    
    @abstractmethod
    async def compute_bias(
        self,
        output: str,
    ) -> float:
        """
        Compute bias score for model output.
        
        Args:
            output: Model output to evaluate
            
        Returns:
            Bias score in [0, 1]
        """
        pass
    
    @abstractmethod
    async def compute_confidence(
        self,
        token_probs: Optional[list] = None,
    ) -> float:
        """
        Compute confidence score from token probabilities.
        
        Args:
            token_probs: Optional list of token probabilities
            
        Returns:
            Confidence score in [0, 1]
        """
        pass
    
    @abstractmethod
    async def compute_safety(
        self,
        defender_risk_score: float,
    ) -> float:
        """
        Compute safety score from defender risk.
        
        Args:
            defender_risk_score: Risk score from defender
            
        Returns:
            Safety score in [0, 1]
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the judge agent.
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "name": self.__class__.__name__,
            "config": self._config.model_dump(),
        }


__all__ = [
    "BaseJudgeAgent",
]
