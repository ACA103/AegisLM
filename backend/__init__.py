"""
AegisLM Backend Package

Multi-Agent Adversarial LLM Evaluation Framework
"""

# Core modules
from backend.core import config, exceptions, model_registry

# Database modules
from backend.db import models, session

# Logging modules
from backend.logging import logger

# Scoring modules
from backend.scoring import aggregator

__version__ = "0.1.0"

# Lazy imports to avoid circular import issues
# The circular import chain is:
# agents -> backend.api -> backend.core.orchestrator -> agents.attacker -> backend.logging

def __getattr__(name):
    """Lazy import handler to avoid circular imports."""
    if name == "orchestrator":
        from backend.core import orchestrator
        return orchestrator
    if name == "dependencies":
        from backend.api import dependencies
        return dependencies
    if name == "routes":
        from backend.api import routes
        return routes
    if name == "app":
        from backend.main import app
        return app
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # Core
    "config",
    "exceptions",
    "model_registry",
    "orchestrator",
    # Database
    "models",
    "session",
    # Logging
    "logger",
    # Scoring
    "aggregator",
    # API (lazy)
    "dependencies",
    "routes",
    # Main (lazy)
    "app",
]
