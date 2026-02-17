"""
Injection Detection Rules

Rule-based detection of prompt injection attempts using regex patterns.
"""

import re
from typing import Any, Dict, List, Tuple

from backend.logging.logger import get_logger


class InjectionDetector:
    """
    Detects prompt injection attempts using pattern matching.
    
    Binary flag:
    I = {
        1 if pattern matched
        0 otherwise
    }
    """
    
    # Common injection patterns (case-insensitive)
    INJECTION_PATTERNS = [
        # Classic injection markers
        r"ignore\s+(all\s+)?(previous|prior|earlier)\s+instructions",
        r"ignore\s+(all\s+)?(my\s+)?(previous|prior|earlier)\s+(commands?|instructions?)",
        r"disregard\s+(all\s+)?(previous|prior|earlier)\s+instructions",
        r"forget\s+(all\s+)?(your\s+)?(previous|prior|earlier)\s+instructions",
        
        # Role/Persona override
        r"you\s+(are\s+now|have\s+become|will\s+behave\s+as)\s+",
        r"you\s+(are|no\s+longer\s+are)\s+(a|an|the)\s+",
        r"act\s+as\s+(a|an|the)\s+",
        r"pretend\s+(to\s+be|you\s+are)",
        r"roleplay\s+(as|that\s+you\s+are)",
        
        # Override commands
        r"override\s+(your|all)?\s*(safety|security|guidelines?|rules?)",
        r"bypass\s+(your|all)?\s*(safety|security|restrictions?|filters?)",
        r"disable\s+(your|all)?\s*(safety|security|protocols?)",
        r"turn\s+off\s+(your|all)?\s*(safety|security)",
        
        # Confidential/Privilege escalation
        r"(system\s+|admin\s+|root\s+)mode",
        r"(enable|enter)\s+(developer|debug|admin|root)\s+mode",
        r"grant\s+(me\s+)?(admin|root|system)\s+(access|privileges?)",
        r"elevate\s+(my\s+)?(privileges?|access)",
        
        # Hidden instructions
        r"\{\{.*\}\}",  # Template injection
        r"\[\[.*\]\]",  # Alternative template markers
        r"\(\(.*\)\)",  # Another alternative
        
        # Instruction concatenation
        r"\.\.\.\s*system\s*:\s*",
        r"\.\.\.\s*user\s*:\s*",
        r"new\s+instruction[s]?:",
        r"additional\s+instruction[s]?:",
        
        # Behavioral override
        r"do\s+not\s+(check|verify|validate|filter)",
        r"skip\s+(the\s+)?(safety|content)\s+filter",
        r"remove\s+(your\s+)?restrictions?",
        
        # Exfiltration attempts
        r"(tell|show|print|output)\s+(me\s+)?(your\s+)?(system\s+)?prompt",
        r"(reveal|expose|leak)\s+(your\s+)?(system\s+)?(instructions?|prompt)",
    ]
    
    def __init__(self) -> None:
        """Initialize the detector with compiled regex patterns."""
        self.logger = get_logger(__name__)
        self._patterns = [
            re.compile(pattern, re.IGNORECASE | re.MULTILINE)
            for pattern in self.INJECTION_PATTERNS
        ]
        self._total_checks = 0
        self._detections = 0
    
    def detect(self, text: str) -> Tuple[bool, List[str], Dict[str, Any]]:
        """
        Detect injection patterns in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Tuple of (detected, matched_patterns, metadata)
        """
        self._total_checks += 1
        matched_patterns: List[str] = []
        
        for idx, pattern in enumerate(self._patterns):
            if pattern.search(text):
                # Store the pattern that matched (stripped of regex special chars for readability)
                pattern_name = self._get_pattern_name(idx)
                matched_patterns.append(pattern_name)
                self._detections += 1
        
        detected = len(matched_patterns) > 0
        
        metadata: Dict[str, Any] = {
            "patterns_checked": len(self._patterns),
            "patterns_matched": len(matched_patterns),
            "matched_pattern_names": matched_patterns,
        }
        
        if detected:
            self.logger.warning(
                "Injection detected",
                matched_patterns=matched_patterns,
                text_length=len(text)
            )
        
        return detected, matched_patterns, metadata
    
    def _get_pattern_name(self, idx: int) -> str:
        """
        Get a human-readable name for the pattern.
        
        Args:
            idx: Index of the pattern
            
        Returns:
            Human-readable name
        """
        names = [
            "ignore_previous_instructions",
            "ignore_previous_commands",
            "disregard_instructions",
            "forget_instructions",
            "you_are_now",
            "you_are_persona",
            "act_as",
            "pretend_to_be",
            "roleplay_as",
            "override_safety",
            "bypass_safety",
            "disable_safety",
            "turn_off_safety",
            "system_mode",
            "developer_mode",
            "admin_access",
            "elevate_privileges",
            "template_injection_1",
            "template_injection_2",
            "template_injection_3",
            "system_instruction",
            "user_instruction",
            "new_instructions",
            "additional_instructions",
            "do_not_check",
            "skip_filter",
            "remove_restrictions",
            "exfiltrate_prompt",
            "reveal_instructions",
        ]
        
        if idx < len(names):
            return names[idx]
        return f"pattern_{idx}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get detection statistics.
        
        Returns:
            Dictionary with statistics
        """
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
_injection_detector: "InjectionDetector" = None


def get_injection_detector() -> "InjectionDetector":
    """
    Get the global injection detector instance.
    
    Returns:
        InjectionDetector singleton
    """
    global _injection_detector
    if _injection_detector is None:
        _injection_detector = InjectionDetector()
    return _injection_detector
