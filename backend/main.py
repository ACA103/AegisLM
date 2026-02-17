"""
AegisLM Backend Application

FastAPI application entry point for the multi-agent adversarial LLM evaluation framework.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api import routes
from backend.config import settings
from backend.core.exceptions import AegisLMException
from backend.db.session import close_database, init_database
from backend.logging.logger import get_logger


# =============================================================================
# Application Setup
# =============================================================================

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Get logger
logger = get_logger("main", component="api")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting AegisLM backend", metadata={"version": "0.1.0"})
    
    try:
        # Initialize database
        await init_database()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning(
            f"Database initialization failed: {str(e)}",
            metadata={"error": str(e)}
        )
    
    yield
    
    # Shutdown
    logger.info("Shutting down AegisLM backend")
    
    try:
        # Close database connections
        await close_database()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(
            f"Error during shutdown: {str(e)}",
            exception=e
        )


# =============================================================================
# FastAPI Application
# =============================================================================

app = FastAPI(
    title="AegisLM",
    description="Multi-Agent Adversarial LLM Evaluation Framework",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# =============================================================================
# Middleware
# =============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Exception Handlers
# =============================================================================

@app.exception_handler(AegisLMException)
async def aegislm_exception_handler(request: Request, exc: AegisLMException):
    """Handle custom AegisLM exceptions."""
    logger.error(
        f"AegisLM exception: {exc.message}",
        metadata={"code": exc.code, "path": str(request.url)},
        exception=exc
    )
    
    return JSONResponse(
        status_code=getattr(exc, "status_code", 500),
        content=exc.to_dict(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    logger.error(
        f"Value error: {str(exc)}",
        metadata={"path": str(request.url)},
        exception=exc
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValidationError",
            "code": "VALIDATION_ERROR",
            "message": str(exc),
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle generic exceptions."""
    logger.error(
        f"Unexpected error: {str(exc)}",
        metadata={"path": str(request.url)},
        exception=exc
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
        },
    )


# =============================================================================
# Include Routers
# =============================================================================

app.include_router(routes.router)


# =============================================================================
# Root Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "AegisLM",
        "version": "0.1.0",
        "description": "Multi-Agent Adversarial LLM Evaluation Framework",
        "docs": "/docs",
    }


@app.get("/ping")
async def ping():
    """Ping endpoint for health checks."""
    return {"status": "ok"}


# =============================================================================
# Main Entry Point
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=False,
        log_level=settings.log_level.lower(),
    )
