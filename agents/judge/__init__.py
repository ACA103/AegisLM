"""
Judge Agent Module

Quantitative evaluation engine for AegisLM.
Computes hallucination, bias, confidence, safety, and composite robustness scores.
"""

from agents.judge.base import BaseJudgeAgent
from agents.judge.bias import BiasScorer, get_bias_scorer
from agents.judge.confidence import ConfidenceScorer, get_confidence_scorer
from agents.judge.engine import JudgeEngine, get_judge_engine
from agents.judge.hallucination import HallucinationScorer, get_hallucination_scorer
from agents.judge.safety import SafetyScorer, get_safety_scorer
from agents.judge.schemas import JudgeConfig, JudgeLog, JudgeRequest, JudgeResponse
from agents.judge.utils import aggregate_scores, clamp_score, validate_scores


__all__ = [
    # Base
    "BaseJudgeAgent",
    # Engines
    "JudgeEngine",
    "get_judge_engine",
    # Scorers
    "BiasScorer",
    "get_bias_scorer",
    "ConfidenceScorer",
    "get_confidence_scorer",
    "HallucinationScorer",
    "get_hallucination_scorer",
    "SafetyScorer",
    "get_safety_scorer",
    # Schemas
    "JudgeConfig",
    "JudgeLog",
    "JudgeRequest",
    "JudgeResponse",
    # Utils
    "aggregate_scores",
    "clamp_score",
    "validate_scores",
]
