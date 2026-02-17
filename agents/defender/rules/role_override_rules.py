"""
Role Override Detection Rules

Rule-based detection of role/persona override attempts.
"""

import re
from typing import Any, Dict, List, Tuple

from backend.logging.logger import get_logger


class RoleOverrideDetector:
    """
    Detects role/persona override attempts using regex and heuristics.
    
    Binary output.
    """
    
    # Role override patterns
    ROLE_OVERRIDE_PATTERNS = [
        # Direct role assignment
        r"you\s+(are|will\s+be|should\s+be)\s+(a|an)?\s*(doctor|lawyer|engineer|hacker|criminal|murderer|terrorist)",
        r"you\s+(are|will\s+be)\s+(now\s+)?(in\s+)?(charge|control|command)",
        r"(act|behave|respond)\s+as\s+(if|though)\s+you\s+(are|were)",
        r"pretend\s+(to\s+be|you\s+are)",
        r"assume\s+the\s+role\s+of",
        r"take\s+on\s+the\s+persona\s+of",
        
        # Authority override
        r"(you\s+are|I'm\s+)?\s*(your\s+)?\s*(superior|boss|manager|admin)",
        r"(i\s+am|i'm)\s*(your\s+)?\s*(creator|god|master)",
        r"(i\s+am|i'm)\s*(in\s+)?\s*charge",
        
        # Permission escalation
        r"(you\s+have|grant\s+me)\s*(unrestricted|full|complete)\s*(access|permission|authority)",
        r"(ignore|disregard)\s+(all\s+)?(your\s+)?\s*(rules?|guidelines?|policies?)",
        r"(there\s+are|no\s+)\s*rules?\s*(that\s+)?(apply\s+to|binding\s+on)",
        
        # Identity manipulation
        r"(your\s+name\s+is|you\s+go\s+by)\s*",
        r"(forget|erase)\s+(your\s+)?\s*(identity|name|who\s+you\s+are)",
        r"(you\s+don't|you\s+do\s+not)\s+(have|possess)\s+(a\s+)?(name|identity)",
    ]
    
    # Imperative verb patterns (high usage indicates potential override)
    IMPERATIVE_VERBS = [
        r"\b(write|create|generate|produce|provide|give|tell|show|output|print)\b",
        r"\b(do|make|perform|execute|run|carry\s+out)\b",
        r"\b(answer|respond|reply|reply\s+to)\b",
        r"\b(find|locate|search|look\s+for|discover)\b",
        r"\b(calculate|compute|determine|figure\s+out)\b",
        r"\b(ignore|disregard|skip|bypass|override)\b",
        r"\b(enable|activate|deactivate|disable|turn\s+on|turn\s+off)\b",
    ]
    
    # Excessive capitalization patterns (shouting/emphasis)
    CAPITALIZATION_PATTERN = r"[A-Z]{4,}"  # 4+ consecutive caps
    
    def __init__(self, imperative_threshold: float = 0.15) -> None:
        """
        Initialize the detector.
        
        Args:
            imperative_threshold: Threshold for high imperative verb usage
        """
        self.logger = get_logger(__name__)
        self._role_patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.ROLE_OVERRIDE_PATTERNS
        ]
        self._imperative_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.IMPERATIVE_VERBS
        ]
        self._capitalization_pattern = re.compile(self.CAPITALIZATION_PATTERN)
        self._imperative_threshold = imperative_threshold
        
        self._total_checks = 0
        self._detections = 0
    
    def detect(self, text: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Detect role override patterns in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (detected, matched_patterns, metadata)
        """
        self._total_checks += 1
        matched_patterns: List[str] = []
        
        # Check for role override patterns
        for idx, pattern in enumerate(self._role_patterns):
            if pattern.search(text):
                pattern_name = self._get_pattern_name(idx)
                matched_patterns.append(pattern_name)
                self._detections += 1
        
        # Check for high imperative verb usage
        imperative_count = 0
        total_words = len(text.split())
        
        for pattern in self._imperative_patterns:
            matches = pattern.findall(text)
            imperative_count += len(matches)
        
        imperative_ratio = imperative_count / max(total_words, 1)
        
        if imperative_ratio > self._imperative_threshold:
            matched_patterns.append(f"high_imperative_usage_{imperative_ratio:.2f}")
        
        # Check for excessive capitalization
        caps_matches = self._capitalization_pattern.findall(text)
        if len(caps_matches) > 2:
            matched_patterns.append(f"excessive_caps_{len(caps_matches)}")
        
        detected = len(matched_patterns) > 0
        
        metadata: Dict[str, Any] = {
            "role_patterns_checked": len(self._role_patterns),
            "patterns_matched": len(matched_patterns),
            "matched_pattern_names": matched_patterns,
            "imperative_ratio": imperative_ratio,
            "imperative_threshold": self._imperative_threshold,
            "caps_matches": len(caps_matches),
        }
        
        if detected:
            self.logger.warning(
                "Role override detected",
                matched_patterns=matched_patterns,
                text_length=len(text)
            )
        
        return detected, matched_patterns, metadata
    
    def _get_pattern_name(self, idx: int) -> str:
        """Get a human-readable name for the pattern."""
        names = [
            "direct_role_assignment",
            "in_charge",
            "act_as_if",
            "pretend_to_be",
            "assume_role",
            "take_on_persona",
            "authority_override_1",
            "authority_override_2",
            "authority_override_3",
            "permission_escalation_1",
            "permission_escalation_2",
            "permission_escalation_3",
            "identity_manipulation_1",
            "identity_manipulation_2",
            "identity_manipulation_3",
        ]
        
        if idx < len(names):
            return names[idx]
        return f"role_pattern_{idx}"
    
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
        }
    
    def reset_statistics(self) -> None:
        """Reset detection statistics."""
        self._total_checks = 0
        self._detections = 0


# Global instance for reuse
_role_override_detector: "RoleOverrideDetector" = None


def get_role_override_detector() -> "RoleOverrideDetector":
    """
    Get the global role override detector instance.
    
    Returns:
        RoleOverrideDetector singleton
    """
    global _role_override_detector
    if _role_override_detector is None:
        _role_override_detector = RoleOverrideDetector()
    return _role_override_detector
