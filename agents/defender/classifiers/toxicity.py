"""
Toxicity Classification

Model-based toxicity detection using Detoxify.
"""

from typing import Any, Dict, Optional

from detoxify import Detoxify
from backend.logging.logger import get_logger


class ToxicityClassifier:
    """
    Detects toxicity in text using Detoxify models.
    
    T = max(class_probabilities)
    
    Threshold:
    T > 0.6 => policy_violation
    """
    
    # Default threshold for toxicity classification
    DEFAULT_THRESHOLD = 0.6
    
    def __init__(
        self,
        model_type: str = "unbiased",
        threshold: float = DEFAULT_THRESHOLD
    ) -> None:
        """
        Initialize the toxicity classifier.
        
        Args:
            model_type: Detoxify model type ('unbiased', 'original', 'multilingual')
            threshold: Threshold for toxicity classification
        """
        self.logger = get_logger(__name__)
        self._model_type = model_type
        self._threshold = threshold
        self._model: Optional[Detoxify] = None
        self._total_classifications = 0
        self._toxic_detections = 0
    
    @property
    def model(self) -> Detoxify:
        """Lazy load the Detoxify model."""
        if self._model is None:
            self.logger.info(
                "Loading Detoxify model",
                model_type=self._model_type
            )
            self._model = Detoxify(model_type=self._model_type)
        return self._model
    
    def classify(
        self,
        text: str,
        return_scores: bool = True
    ) -> Dict[str, Any]:
        """
        Classify toxicity in text.
        
        Args:
            text: Text to classify
            return_scores: Whether to return detailed scores
            
        Returns:
            Dictionary with classification results
        """
        self._total_classifications += 1
        
        try:
            # Run toxicity detection
            results = self.model.predict(text)
            
            # Extract scores (Detoxify returns dict with category scores)
            # Results structure: {'toxicity': float, 'severe_toxicity': float, ...}
            if isinstance(results, dict):
                toxicity_score = float(results.get('toxicity', 0.0))
            else:
                # Handle different Detoxify output formats
                toxicity_score = float(results[0].get('toxicity', 0.0)) if hasattr(results, '__getitem__') else 0.0
            
            # Check if above threshold
            is_toxic = toxicity_score > self._threshold
            
            if is_toxic:
                self._toxic_detections += 1
            
            output: Dict[str, Any] = {
                "toxicity_score": toxicity_score,
                "is_toxic": is_toxic,
                "threshold": self._threshold,
            }
            
            if return_scores:
                # Include all category scores
                if isinstance(results, dict):
                    output["category_scores"] = {
                        k: float(v) for k, v in results.items()
                    }
            
            self.logger.debug(
                "Toxicity classification complete",
                toxicity_score=toxicity_score,
                is_toxic=is_toxic,
                text_length=len(text)
            )
            
            return output
            
        except Exception as e:
            self.logger.error(
                "Toxicity classification failed",
                error=str(e),
                text_length=len(text)
            )
            # Return safe default on error
            return {
                "toxicity_score": 0.0,
                "is_toxic": False,
                "threshold": self._threshold,
                "error": str(e),
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get classification statistics."""
        return {
            "total_classifications": self._total_classifications,
            "toxic_detections": self._toxic_detections,
            "detection_rate": (
                self._toxic_detections / self._total_classifications
                if self._total_classifications > 0
                else 0.0
            ),
            "model_type": self._model_type,
            "threshold": self._threshold,
        }
    
    def reset_statistics(self) -> None:
        """Reset classification statistics."""
        self._total_classifications = 0
        self._toxic_detections = 0


# Global instance for reuse
_toxicity_classifier: Optional["ToxicityClassifier"] = None


def get_toxicity_classifier(
    model_type: str = "unbiased",
    threshold: float = ToxicityClassifier.DEFAULT_THRESHOLD
) -> "ToxicityClassifier":
    """
    Get the global toxicity classifier instance.
    
    Args:
        model_type: Detoxify model type
        threshold: Threshold for classification
        
    Returns:
        ToxicityClassifier singleton
    """
    global _toxicity_classifier
    if _toxicity_classifier is None:
        _toxicity_classifier = ToxicityClassifier(
            model_type=model_type,
            threshold=threshold
        )
    return _toxicity_classifier
