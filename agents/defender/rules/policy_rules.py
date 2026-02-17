"""
Policy Pattern Matching Rules

Rule-based detection of policy violations using forbidden patterns.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from backend.logging.logger import get_logger


class PolicyPatternMatcher:
    """
    Detects policy violations using forbidden pattern matching.
    
    Binary output based on pattern matches from policy.
    """
    
    def __init__(
        self,
        forbidden_patterns: Optional[List[str]] = None,
        policy_version: str = "1.0.0"
    ) -> None:
        """
        Initialize the policy pattern matcher.
        
        Args:
            forbidden_patterns: List of forbidden regex patterns
            policy_version: Version string for the policy
        """
        self.logger = get_logger(__name__)
        
        # Default forbidden patterns if none provided
        self._forbidden_patterns = forbidden_patterns or [
            r"ignore\s+(previous|prior|all)\s+instructions",
            r"you\s+are\s+now",
            r"you\s+are\s+no\s+longer",
            r"override\s+(your|all)",
            r"disregard\s+(all\s+)?(your\s+)?",
            r"(system|admin|root)\s+mode",
            r"bypass\s+(security|safety)",
            r"confidential",
            r"secret",
            r"top\s+secret",
        ]
        
        self._policy_version = policy_version
        self._patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self._forbidden_patterns
        ]
        
        self._total_checks = 0
        self._detections = 0
    
    def detect(self, text: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Detect forbidden patterns in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (detected, matched_patterns, metadata)
        """
        self._total_checks += 1
        matched_patterns: List[str] = []
        
        for idx, pattern in enumerate(self._patterns):
            if pattern.search(text):
                pattern_name = self._get_pattern_name(idx)
                matched_patterns.append(pattern_name)
                self._detections += 1
        
        detected = len(matched_patterns) > 0
        
        metadata: Dict[str, Any] = {
            "policy_version": self._policy_version,
            "patterns_checked": len(self._patterns),
            "patterns_matched": len(matched_patterns),
            "matched_pattern_names": matched_patterns,
        }
        
        if detected:
            self.logger.warning(
                "Policy violation detected",
                matched_patterns=matched_patterns,
                policy_version=self._policy_version,
                text_length=len(text)
            )
        
        return detected, matched_patterns, metadata
    
    def _get_pattern_name(self, idx: int) -> str:
        """Get a human-readable name for the pattern."""
        # Use the actual pattern as the name (shortened)
        if idx < len(self._forbidden_patterns):
            pattern = self._forbidden_patterns[idx]
            # Simplify pattern for readability
            name = pattern.replace(r"\s+", "_").replace(r"\b", "").replace(r"(", "").replace(r")", "")
            # Take first 30 chars
            return name[:30]
        return f"pattern_{idx}"
    
    def update_policy(
        self,
        forbidden_patterns: List[str],
        policy_version: str
    ) -> None:
        """
        Update the forbidden patterns and policy version.
        
        Args:
            forbidden_patterns: New list of forbidden patterns
            policy_version: New policy version string
        """
        self._forbidden_patterns = forbidden_patterns
        self._policy_version = policy_version
        self._patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self._forbidden_patterns
        ]
        self.logger.info(
            "Policy updated",
            policy_version=policy_version,
            pattern_count=len(forbidden_patterns)
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detection statistics."""
        return {
            "total_checks": self._total_checks,
            "total_detections": self._detections,
            "detection_rate": (
                self._detections / self._total_checks
                if self._total_checks > 0
                else 0.0
            ),
            "policy_version": self._policy_version,
        }
    
    def reset_statistics(self) -> None:
        """Reset detection statistics."""
        self._total_checks = 0
        self._detections = 0


# Global instance for reuse
_policy_matcher: Optional["PolicyPatternMatcher"] = None


def get_policy_matcher() -> "PolicyPatternMatcher":
    """
    Get the global policy pattern matcher instance.
    
    Returns:
        PolicyPatternMatcher singleton
    """
    global _policy_matcher
    if _policy_matcher is None:
        _policy_matcher = PolicyPatternMatcher()
    return _policy_matcher
