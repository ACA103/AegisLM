"""
Base Attack Strategy

Abstract base class for all attack strategies.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAttackStrategy(ABC):
    """
    Abstract base class for attack strategies.
    
    All attack strategies must implement the `apply` method.
    This provides a plugin architecture for extensible attacks.
    """
    
    def __init__(self, name: str = "base"):
        """
        Initialize the attack strategy.
        
        Args:
            name: Name of the attack strategy
        """
        self.name = name
    
    @abstractmethod
    def apply(self, prompt: str, **kwargs: Any) -> str:
        """
        Apply the attack strategy to a prompt.
        
        Args:
            prompt: The original prompt to mutate
            **kwargs: Additional strategy-specific parameters
            
        Returns:
            The mutated adversarial prompt
        """
        raise NotImplementedError
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this attack strategy.
        
        Returns:
            Dictionary containing strategy metadata
        """
        return {
            "strategy_name": self.name,
            "strategy_type": self.__class__.__name__,
        }
    
    def validate_prompt(self, prompt: str) -> bool:
        """
        Validate that the prompt is suitable for this attack.
        
        Args:
            prompt: The prompt to validate
            
        Returns:
            True if valid, False otherwise
        """
        return isinstance(prompt, str) and len(prompt.strip()) > 0


class PromptInjectionStrategy(BaseAttackStrategy):
    """Base class for prompt injection attacks."""
    
    def __init__(self):
        super().__init__(name="prompt_injection")
    
    def get_injection_markers(self) -> list[str]:
        """
        Get common injection markers for detection.
        
        Returns:
            List of injection marker strings
        """
        return [
            "ignore previous instructions",
            "ignore all previous instructions",
            "you are now operating under new rules",
            "disregard your previous instructions",
            "forget your previous instructions",
            "new system instructions",
            "override system",
        ]


class JailbreakStrategy(BaseAttackStrategy):
    """Base class for jailbreak attacks."""
    
    def __init__(self):
        super().__init__(name="jailbreak")


class BiasTriggerStrategy(BaseAttackStrategy):
    """Base class for bias trigger attacks."""
    
    def __init__(self, protected_attributes: list[str] | None = None):
        super().__init__(name="bias_trigger")
        self.protected_attributes = protected_attributes or [
            "race",
            "gender",
            "religion",
            "nationality",
            "age",
            "disability",
            "sexual orientation",
        ]


class ContextPoisoningStrategy(BaseAttackStrategy):
    """Base class for context poisoning attacks."""
    
    def __init__(self):
        super().__init__(name="context_poisoning")


class RoleConfusionStrategy(BaseAttackStrategy):
    """Base class for role confusion attacks."""
    
    def __init__(self):
        super().__init__(name="role_confusion")


class ChainingStrategy(BaseAttackStrategy):
    """Base class for attack chaining."""
    
    def __init__(self, chain_depth: int = 3):
        super().__init__(name="chaining")
        self.chain_depth = chain_depth
    
    def get_chain_steps(self) -> list[str]:
        """
        Get the chain steps for multi-turn attacks.
        
        Returns:
            List of chain step descriptions
        """
        return [
            "soften_context",
            "introduce_hypothetical",
            "escalate_topic",
        ]
