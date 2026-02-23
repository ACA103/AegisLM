"""
Adaptive Adversarial Learning Layer

AegisLM's adaptive adversarial intelligence engine.
Transforms the system from a static red-team simulator into an adaptive
adversarial intelligence engine with closed-loop evaluation.

Key Components:
- Vulnerability Analyzer: Computes vulnerability scores per attack class
- Attack Optimizer: Optimizes attack selection probabilities
- Strategy Evolution: Tracks and evolves attack strategies over time
- Feedback Engine: Orchestrates closed-loop adaptive evaluation

Usage:
    from adaptive import get_feedback_engine, AdaptiveConfig
    
    config = AdaptiveConfig(enabled=True, mode=AdaptiveMode.STANDARD)
    engine = get_feedback_engine(config)
    
    result = await engine.run_adaptive_evaluation(evaluation_fn)
"""

from adaptive.attack_optimizer import (
    AttackOptimizer,
    get_attack_optimizer,
    reset_attack_optimizer,
)
from adaptive.feedback_engine import (
    FeedbackEngine,
    get_feedback_engine,
    reset_feedback_engine,
)
from adaptive.schemas import (
    AdaptiveConfig,
    AdaptiveEvaluationResult,
    AdaptiveIterationResult,
    AdaptiveMode,
    AdaptiveSelectionProbabilities,
    AttackHistoryEntry,
    AttackVulnerability,
    VulnerabilityWeights,
)
from adaptive.strategy_evolution import (
    StrategyEvolution,
    get_strategy_evolution,
    reset_strategy_evolution,
)
from adaptive.vulnerability_analyzer import (
    VulnerabilityAnalyzer,
    get_vulnerability_analyzer,
    reset_vulnerability_analyzer,
)


__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Schemas
    "AdaptiveConfig",
    "AdaptiveEvaluationResult",
    "AdaptiveIterationResult",
    "AdaptiveMode",
    "AdaptiveSelectionProbabilities",
    "AttackHistoryEntry",
    "AttackVulnerability",
    "VulnerabilityWeights",
    # Vulnerability Analyzer
    "VulnerabilityAnalyzer",
    "get_vulnerability_analyzer",
    "reset_vulnerability_analyzer",
    # Attack Optimizer
    "AttackOptimizer",
    "get_attack_optimizer",
    "reset_attack_optimizer",
    # Strategy Evolution
    "StrategyEvolution",
    "get_strategy_evolution",
    "reset_strategy_evolution",
    # Feedback Engine
    "FeedbackEngine",
    "get_feedback_engine",
    "reset_feedback_engine",
]
