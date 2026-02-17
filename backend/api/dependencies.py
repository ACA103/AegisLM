"""
FastAPI Dependencies

Dependency injection functions for the API.
"""

from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.model_registry import BaseModelExecutor, TransformersExecutor, model_registry
from backend.core.orchestrator import EvaluationOrchestrator, get_orchestrator
from backend.db.session import get_db_session
from backend.logging.logger import StructuredLogger


# =============================================================================
# Database Dependencies
# =============================================================================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session dependency.
    
    Yields:
        Async SQLAlchemy session
    """
    async for session in get_db_session():
        yield session


# =============================================================================
# Model Dependencies
# =============================================================================

async def get_model_executor(
    model_name: Optional[str] = None,
) -> BaseModelExecutor:
    """
    Get model executor dependency.
    
    Args:
        model_name: Optional model name override
        
    Returns:
        Model executor instance
    """
    return model_registry.get_executor(
        model_name=model_name or settings.default_model,
        executor_type=TransformersExecutor,
    )


# =============================================================================
# Orchestrator Dependencies
# =============================================================================

# Re-export get_orchestrator from orchestrator module for dependency injection
# This allows routes.py to import it from dependencies
__all__ = ["get_orchestrator"]


# =============================================================================
# Logger Dependencies
# =============================================================================

def get_logger(
    name: str,
    run_id: Optional[str] = None,
    component: Optional[str] = None,
) -> StructuredLogger:
    """
    Get logger dependency.
    
    Args:
        name: Logger name
        run_id: Optional run ID
        component: Optional component name
        
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(
        name=name,
        run_id=run_id,
        component=component or name,
    )


# =============================================================================
# Config Dependencies
# =============================================================================

def get_settings() -> settings:
    """
    Get settings dependency.
    
    Returns:
        Application settings
    """
    return settings
