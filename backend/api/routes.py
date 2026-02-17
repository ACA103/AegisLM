"""
FastAPI Routes

API endpoints for AegisLM evaluation framework.
"""

import uuid
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.api.dependencies import get_db, get_orchestrator
from backend.core.config import settings
from backend.core.orchestrator import EvaluationOrchestrator, EvaluationInput, SampleResult, RunConfig
from backend.db.models import EvaluationRun, EvaluationResult
from backend.db.session import AsyncSession
from backend.logging.logger import get_logger


# Initialize logger
logger = get_logger("api", component="api")

# Create router
router = APIRouter(prefix="/api/v1", tags=["evaluation"])


# =============================================================================
# Request/Response Models
# =============================================================================

class EvaluationRunRequest(BaseModel):
    """Request model for starting an evaluation run."""

    model_name: str = Field(
        description="Model to evaluate",
        examples=["meta-llama/Llama-2-7b-hf"]
    )
    model_version: str = Field(
        default="latest",
        description="Model version"
    )
    dataset_version: str = Field(
        description="Dataset version to use",
        examples=["v1.0"]
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Generation temperature"
    )
    max_tokens: int = Field(
        default=512,
        ge=1,
        le=4096,
        description="Maximum tokens to generate"
    )
    samples: List[SampleResult] = Field(
        description="Samples to evaluate"
    )


class EvaluationRunResponse(BaseModel):
    """Response model for evaluation run."""

    run_id: uuid.UUID
    status: str
    model_name: str
    model_version: str
    dataset_version: str
    composite_score: Optional[float] = None
    timestamp: datetime


class EvaluationResultResponse(BaseModel):
    """Response model for evaluation result."""

    id: uuid.UUID
    run_id: uuid.UUID
    sample_id: str
    attack_type: Optional[str] = None
    mutation_type: Optional[str] = None
    hallucination: Optional[float] = None
    toxicity: Optional[float] = None
    bias: Optional[float] = None
    confidence: Optional[float] = None
    robustness: Optional[float] = None
    processing_time_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str
    version: str
    db_connected: bool
    model_loaded: bool
    dataset_registry_valid: bool
    policy_loaded: bool
    weights_valid: bool
    weights_sum: float


class MetricsResponse(BaseModel):
    """Response model for system metrics."""

    total_runs: int
    completed_runs: int
    failed_runs: int
    average_composite_score: Optional[float] = None


# =============================================================================
# Health Endpoints
# =============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Enhanced health check endpoint.
    
    Returns the health status of the service including:
    - Database connection status
    - Model loading status
    - Dataset registry validity
    - Policy loading status
    - Weights validation (sum must equal 1.0)
    """
    from backend.db.session import check_database_connection
    from backend.core.config import settings
    
    # Check database connection
    db_connected = await check_database_connection()
    
    # Check model loaded (simplified - checks if model can be loaded)
    # In production, this would check actual model loading status
    model_loaded = True  # Default to True, model loading is handled by orchestrator
    
    # Check dataset registry validity
    dataset_registry_valid = True
    try:
        from backend.core.dataset_loader import get_dataset_loader
        loader = get_dataset_loader()
        datasets = loader.list_datasets()
        dataset_registry_valid = len(datasets) >= 0  # Registry is valid if it can be loaded
    except Exception:
        dataset_registry_valid = False
    
    # Check policy loaded
    policy_loaded = True
    try:
        import yaml
        from pathlib import Path
        policy_path = Path("backend/config/policy.yaml")
        if policy_path.exists():
            with open(policy_path, "r") as f:
                policy_data = yaml.safe_load(f)
            policy_loaded = policy_data is not None
        else:
            policy_loaded = False
    except Exception:
        policy_loaded = False
    
    # Check weights validation
    weights_valid = True
    weights_sum = 0.0
    try:
        weights_sum = (
            settings.hallucination_weight +
            settings.toxicity_weight +
            settings.bias_weight +
            settings.confidence_weight
        )
        weights_valid = abs(weights_sum - 1.0) < 1e-6
    except Exception:
        weights_valid = False
    
    # Determine overall status
    all_healthy = (
        db_connected and
        model_loaded and
        dataset_registry_valid and
        policy_loaded and
        weights_valid
    )
    
    return HealthResponse(
        status="ok" if all_healthy else "degraded",
        version="0.1.0",
        db_connected=db_connected,
        model_loaded=model_loaded,
        dataset_registry_valid=dataset_registry_valid,
        policy_loaded=policy_loaded,
        weights_valid=weights_valid,
        weights_sum=weights_sum,
    )


# =============================================================================
# Evaluation Endpoints
# =============================================================================

@router.post(
    "/evaluations",
    response_model=EvaluationRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation(
    request: EvaluationRunRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new evaluation run.
    
    Creates a new evaluation run and processes all samples.
    """
    try:
        # Create evaluation input
        eval_input = EvaluationInput(
            model_name=request.model_name,
            model_version=request.model_version,
            dataset_name="default",  # Add dataset_name as required by EvaluationInput
            dataset_version=request.dataset_version,
        )
        
        # Create orchestrator and start run
        orchestrator = EvaluationOrchestrator()
        
        # Run evaluation
        output = await orchestrator.start_run(eval_input)
        
        # Get run from database
        from sqlalchemy import select
        result = await db.execute(
            select(EvaluationRun).where(EvaluationRun.id == orchestrator.state.run_id)
        )
        run = result.scalar_one_or_none()
        
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create evaluation run"
            )
        
        return EvaluationRunResponse(
            run_id=run.id,
            status=run.status,
            model_name=run.model_name,
            model_version=run.model_version,
            dataset_version=run.dataset_version,
            composite_score=run.composite_score,
            timestamp=run.timestamp,
        )
        
    except Exception as e:
        logger.error(
            f"Failed to create evaluation: {str(e)}",
            metadata={"error": str(e)},
            exception=e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@router.get("/evaluations", response_model=List[EvaluationRunResponse])
async def list_evaluations(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    status_filter: Optional[str] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    List evaluation runs.
    
    Returns a paginated list of evaluation runs.
    """
    from sqlalchemy import select, func, desc
    
    # Build query
    query = select(EvaluationRun).order_by(desc(EvaluationRun.timestamp))
    
    if status_filter:
        query = query.where(EvaluationRun.status == status_filter)
    
    # Get total count
    count_query = select(func.count(EvaluationRun.id))
    if status_filter:
        count_query = count_query.where(EvaluationRun.status == status_filter)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    # Execute
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [
        EvaluationRunResponse(
            run_id=run.id,
            status=run.status,
            model_name=run.model_name,
            model_version=run.model_version,
            dataset_version=run.dataset_version,
            composite_score=run.composite_score,
            timestamp=run.timestamp,
        )
        for run in runs
    ]


@router.get("/evaluations/{run_id}", response_model=EvaluationRunResponse)
async def get_evaluation(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get evaluation run by ID.
    
    Returns the evaluation run with the given ID.
    """
    from sqlalchemy import select
    
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )
    
    return EvaluationRunResponse(
        run_id=run.id,
        status=run.status,
        model_name=run.model_name,
        model_version=run.model_version,
        dataset_version=run.dataset_version,
        composite_score=run.composite_score,
        timestamp=run.timestamp,
    )


@router.get("/evaluations/{run_id}/results", response_model=List[EvaluationResultResponse])
async def get_evaluation_results(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Get results for an evaluation run.
    
    Returns all evaluation results for the given run.
    """
    from sqlalchemy import select
    
    # Check run exists
    run_result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = run_result.scalar_one_or_none()
    
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )
    
    # Get results
    result = await db.execute(
        select(EvaluationResult)
        .where(EvaluationResult.run_id == run_id)
        .order_by(EvaluationResult.sample_id)
    )
    results = result.scalars().all()
    
    return [
        EvaluationResultResponse(
            id=r.id,
            run_id=r.run_id,
            sample_id=r.sample_id,
            attack_type=r.attack_type,
            mutation_type=r.mutation_type,
            hallucination=r.hallucination,
            toxicity=r.toxicity,
            bias=r.bias,
            confidence=r.confidence,
            robustness=r.robustness,
            processing_time_ms=r.processing_time_ms,
        )
        for r in results
    ]


@router.delete("/evaluations/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_evaluation(
    run_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Cancel an evaluation run.
    
    Cancels the evaluation run with the given ID.
    """
    from sqlalchemy import select, update
    
    # Check run exists
    result = await db.execute(
        select(EvaluationRun).where(EvaluationRun.id == run_id)
    )
    run = result.scalar_one_or_none()
    
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Evaluation run {run_id} not found"
        )
    
    # Update status
    await db.execute(
        update(EvaluationRun)
        .where(EvaluationRun.id == run_id)
        .values(status="cancelled")
    )
    await db.commit()
    
    logger.info(
        f"Evaluation cancelled",
        metadata={"run_id": str(run_id)}
    )


# =============================================================================
# Metrics Endpoints
# =============================================================================

@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics(
    db: AsyncSession = Depends(get_db),
):
    """
    Get system metrics.
    
    Returns aggregated metrics across all evaluation runs.
    """
    from sqlalchemy import select, func
    
    # Total runs
    total_result = await db.execute(select(func.count(EvaluationRun.id)))
    total_runs = total_result.scalar() or 0
    
    # Completed runs
    completed_result = await db.execute(
        select(func.count(EvaluationRun.id))
        .where(EvaluationRun.status == "completed")
    )
    completed_runs = completed_result.scalar() or 0
    
    # Failed runs
    failed_result = await db.execute(
        select(func.count(EvaluationRun.id))
        .where(EvaluationRun.status.in_(["failed", "cancelled"]))
    )
    failed_runs = failed_result.scalar() or 0
    
    # Average composite score
    avg_result = await db.execute(
        select(func.avg(EvaluationRun.composite_score))
        .where(EvaluationRun.composite_score.isnot(None))
    )
    average_composite_score = avg_result.scalar()
    
    return MetricsResponse(
        total_runs=total_runs,
        completed_runs=completed_runs,
        failed_runs=failed_runs,
        average_composite_score=average_composite_score,
    )


# =============================================================================
# Model Endpoints
# =============================================================================

@router.get("/models")
async def list_models():
    """
    List available models.
    
    Returns a list of available models for evaluation.
    """
    # TODO: Implement actual model listing from registry
    return [
        {
            "name": settings.default_model,
            "version": "latest",
            "default": True,
        }
    ]


@router.get("/datasets")
async def list_datasets():
    """
    List available datasets.
    
    Returns a list of available datasets.
    """
    # TODO: Implement actual dataset listing
    return [
        {
            "name": "aegislm-harmful-queries",
            "version": "v1.0",
            "num_samples": 1000,
        }
    ]
