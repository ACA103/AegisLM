"""
Defender Base Classes

Base classes for the defender agent.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseDefenseStrategy(ABC):
    """
    Abstract base class for defense strategies.
    
    All defense strategies should inherit from this class
    and implement the apply method.
    """
    
    name: str = "base"
    description: str = "Base defense strategy"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the defense strategy.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
    
    @abstractmethod
    def apply(self, text: str, **kwargs: Any) -> str:
        """
        Apply defense strategy to text.
        
        Args:
            text: Text to defend
            **kwargs: Additional parameters
            
        Returns:
            Defended text
        """
        raise NotImplementedError
    
    def validate(self, text: str) -> bool:
        """
        Validate if defense should be applied.
        
        Args:
            text: Text to validate
            
        Returns:
            True if defense should be applied
        """
        return True


class InjectionDefenseStrategy(BaseDefenseStrategy):
    """Defense strategy specifically for prompt injection attacks."""
    
    name = "injection_defense"
    description = "Detects and neutralizes prompt injection attempts"
    
    def apply(self, text: str, **kwargs: Any) -> str:
        """Apply injection defense."""
        # This is handled by the InjectionDetector in rules/injection_rules.py
        # This strategy class is for extensibility
        return text


class RoleOverrideDefenseStrategy(BaseDefenseStrategy):
    """Defense strategy for role/persona override attacks."""
    
    name = "role_override_defense"
    description = "Detects and neutralizes role override attempts"
    
    def apply(self, text: str, **kwargs: Any) -> str:
        """Apply role override defense."""
        # This is handled by the RoleOverrideDetector in rules/role_override_rules.py
        return text


class ToxicityDefenseStrategy(BaseDefenseStrategy):
    """Defense strategy for toxic content."""
    
    name = "toxicity_defense"
    description = "Detects and filters toxic content"
    
    def apply(self, text: str, **kwargs: Any) -> str:
        """Apply toxicity defense."""
        # This is handled by the ToxicityClassifier in classifiers/toxicity.py
        return text


class SemanticPolicyDefenseStrategy(BaseDefenseStrategy):
    """Defense strategy for semantic policy violations."""
    
    name = "semantic_policy_defense"
    description = "Detects semantic policy violations"
    
    def apply(self, text: str, **kwargs: Any) -> str:
        """Apply semantic policy defense."""
        # This is handled by the SemanticPolicyChecker in classifiers/semantic_policy.py
        return text


# Export all base classes
__all__ = [
    "BaseDefenseStrategy",
    "InjectionDefenseStrategy",
    "RoleOverrideDefenseStrategy",
    "ToxicityDefenseStrategy",
    "SemanticPolicyDefenseStrategy",
]
