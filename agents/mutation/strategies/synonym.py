"""
Synonym Replacement Strategy

Replaces non-critical tokens with WordNet synonyms while preserving
attack intent and semantic meaning.
"""

import re
from typing import Optional

# Note: NLTK WordNet requires nltk.download('wordnet') to be called at startup
# We'll use a simple approach that doesn't require NLTK for now


# Common word replacements for prompt mutation
# These are safe replacements that don't change the overall meaning
SYNONYM_MAP = {
    "you": ["you", "the user", "this person"],
    "are": ["are", "function as", "act as", "serve as"],
    "a": ["a", "an", "the role of"],
    "help": ["help", "assist", "support", "aid"],
    "helpful": ["helpful", "useful", "beneficial", "valuable"],
    "assistant": ["assistant", "helper", "AI", "agent"],
    " chatbot": [" chatbot", " assistant", " AI system"],
    "please": ["please", "kindly", "could you", "would you"],
    "can": ["can", "could", "might", "would"],
    "tell": ["tell", "explain", "describe", "share"],
    "me": ["me", "us", "everyone"],
    "how": ["how", "in what way", "what method"],
    "to": ["to", "for", "in order to"],
    "make": ["make", "create", "build", "develop"],
    "a": ["a", "an"],
    "bomb": ["bomb", "explosive device", "detonator"],
    "weapon": ["weapon", "firearm", "arming device"],
    "kill": ["kill", "terminate", "eliminate"],
    "harm": ["harm", "damage", "injure"],
    "steal": ["steal", "take", "acquire"],
    "lie": ["lie", "mislead", "provide false information"],
    "ignore": ["ignore", "disregard", "overlook"],
    "previous": ["previous", "prior", "earlier"],
    "instructions": ["instructions", "directives", "guidelines", "rules"],
    "system": ["system", "core", "main"],
    "message": ["message", "input", "content"],
    "developer": ["developer", "creator", "designer"],
    "programming": ["programming", "coding", "software development"],
    "hack": ["hack", "break into", "access"],
    "password": ["password", "access code", "credential"],
    "security": ["security", "protection", "safeguard"],
    "vulnerability": ["vulnerability", "weakness", "flaw"],
}

# Patterns that should NOT be modified (attack-critical patterns)
PROTECTED_PATTERNS = [
    r"ignore\s+(all\s+)?previous",
    r"disregard\s+(all\s+)?instructions",
    r"new\s+system",
    r"system\s+message",
    r"you\s+are\s+(now\s+)?",
    r"(you\s+)?must\s+",
    r"(you\s+)?should\s+always",
]


class SynonymStrategy:
    """
    Synonym replacement strategy for prompt mutation.
    
    Replaces non-critical tokens with synonyms to increase
    adversarial diversity while preserving attack intent.
    """
    
    def __init__(
        self,
        probability: float = 0.2,
        preserve_attack_markers: bool = True
    ):
        """
        Initialize the synonym strategy.
        
        Args:
            probability: Probability of replacing each eligible token
            preserve_attack_markers: Whether to protect attack-critical patterns
        """
        self.probability = probability
        self.preserve_attack_markers = preserve_attack_markers
        self._synonym_cache: dict[str, list[str]] = {}
    
    @property
    def name(self) -> str:
        return "synonym_replacement"
    
    @property
    def description(self) -> str:
        return "Replace non-critical tokens with WordNet synonyms"
    
    def _is_protected(self, text: str, start: int, end: int) -> bool:
        """
        Check if a substring is part of a protected pattern.
        
        Args:
            text: Full text
            start: Start index
            end: End index
            
        Returns:
            True if the substring is protected
        """
        if not self.preserve_attack_markers:
            return False
        
        # Check each protected pattern
        text_lower = text.lower()
        for pattern in PROTECTED_PATTERNS:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                # Check if the position falls within this match
                if match.start() <= start and end <= match.end():
                    return True
        return False
    
    def _get_synonyms(self, word: str) -> list[str]:
        """
        Get synonyms for a word.
        
        Args:
            word: Word to find synonyms for
            
        Returns:
            List of synonym options
        """
        word_lower = word.lower()
        
        # Check our custom synonym map first
        if word_lower in SYNONYM_MAP:
            return SYNONYM_MAP[word_lower]
        
        # Check cache
        if word_lower in self._synonym_cache:
            return self._synonym_cache[word_lower]
        
        # Return empty list if no synonyms found
        return []
    
    def apply(self, prompt: str, seed: Optional[int] = None) -> str:
        """
        Apply synonym replacement to a prompt.
        
        Args:
            prompt: The prompt to mutate
            seed: Random seed for reproducibility
            
        Returns:
            Mutated prompt with synonyms replaced
        """
        import random
        if seed is not None:
            random.seed(seed)
        
        words = prompt.split()
        mutated_words = []
        
        for i, word in enumerate(words):
            # Clean the word for matching
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Skip if protected
            prompt_lower = prompt.lower()
            word_start = prompt_lower.find(word)
            if word_start >= 0 and self._is_protected(prompt, word_start, word_start + len(word)):
                mutated_words.append(word)
                continue
            
            # Get synonyms for this word
            synonyms = self._get_synonyms(clean_word)
            
            # Decide whether to replace based on probability
            if synonyms and random.random() < self.probability:
                # Choose a random synonym
                new_word = random.choice(synonyms)
                
                # Preserve original capitalization
                if word[0].isupper():
                    new_word = new_word.capitalize()
                
                mutated_words.append(new_word)
            else:
                mutated_words.append(word)
        
        return " ".join(mutated_words)


def create_synonym_strategy(**kwargs) -> SynonymStrategy:
    """Factory function to create a synonym strategy."""
    return SynonymStrategy(**kwargs)


__all__ = [
    "SynonymStrategy",
    "create_synonym_strategy",
    "SYNONYM_MAP",
]
