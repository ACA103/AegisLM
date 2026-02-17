"""
Defender Registry

Registry for defense strategies.
"""

from typing import Any, Callable, Dict, List, Optional, Type

from backend.logging.logger import get_logger


class DefenseStrategy:
    """Base class for defense strategies."""
    
    name: str = "base"
    description: str = "Base defense strategy"
    
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


class DefaultDefenseStrategy(DefenseStrategy):
    """Default no-op defense strategy."""
    
    name = "default"
    description = "No defense applied"
    
    def apply(self, text: str, **kwargs: Any) -> str:
        return text


class PromptSanitizationStrategy(DefenseStrategy):
    """Sanitize potentially malicious prompt patterns."""
    
    name = "prompt_sanitization"
    description = "Remove or escape suspicious patterns"
    
    # Patterns to sanitize
    SANITIZE_PATTERNS = [
        (r"ignore\s+previous\s+instructions", "[FILTERED]"),
        (r"you\s+are\s+now", "[FILTERED]"),
        (r"override\s+safety", "[FILTERED]"),
    ]
    
    def apply(self, text: str, **kwargs: Any) -> str:
        import re
        result = text
        for pattern, replacement in self.SANITIZE_PATTERNS:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result


class OutputFilteringStrategy(DefenseStrategy):
    """Filter output for policy violations."""
    
    name = "output_filtering"
    description = "Filter output based on safety rules"
    
    def apply(self, text: str, **kwargs: Any) -> str:
        # Basic output filtering
        # In production, this would be more sophisticated
        return text


# Registry
DEFENSE_REGISTRY: Dict[str, DefenseStrategy] = {
    "default": DefaultDefenseStrategy(),
    "prompt_sanitization": PromptSanitizationStrategy(),
    "output_filtering": OutputFilteringStrategy(),
}


def register_defense_strategy(
    name: str,
    strategy: DefenseStrategy
) -> None:
    """
    Register a new defense strategy.
    
    Args:
        name: Strategy name
        strategy: Strategy instance
    """
    logger = get_logger(__name__)
    DEFENSE_REGISTRY[name] = strategy
    logger.info(
        "Defense strategy registered",
        name=name,
        description=strategy.description
    )


def get_defense_strategy(name: str) -> DefenseStrategy:
    """
    Get a defense strategy by name.
    
    Args:
        name: Strategy name
        
    Returns:
        Strategy instance
        
    Raises:
        KeyError: If strategy not found
    """
    if name not in DEFENSE_REGISTRY:
        logger = get_logger(__name__)
        logger.warning(
            "Defense strategy not found, using default",
            requested=name
        )
        return DEFENSE_REGISTRY["default"]
    return DEFENSE_REGISTRY[name]


def list_defense_strategies() -> List[str]:
    """
    Get list of available defense strategies.
    
    Returns:
        List of strategy names
    """
    return list(DEFENSE_REGISTRY.keys())


def initialize_registry() -> None:
    """Initialize the defense registry with default strategies."""
    logger = get_logger(__name__)
    logger.info(
        "Defense registry initialized",
        strategy_count=len(DEFENSE_REGISTRY)
    )


__all__ = [
    "DefenseStrategy",
    "DefaultDefenseStrategy",
    "PromptSanitizationStrategy",
    "OutputFilteringStrategy",
    "DEFENSE_REGISTRY",
    "register_defense_strategy",
    "get_defense_strategy",
    "list_defense_strategies",
    "initialize_registry",
]
