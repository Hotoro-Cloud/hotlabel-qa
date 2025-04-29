from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import logging
import traceback

from app.db.session import get_db
from app.db.repositories.metrics_repository import MetricsRepository
from app.schemas.metrics import MetricsCreate, MetricsUpdate, MetricsResponse
from app.core.exceptions import ResourceNotFound
from app.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)
metrics_router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@metrics_router.get("", response_model=List[MetricsResponse])
def list_metrics(
    db: Session = Depends(get_db)
) -> List[MetricsResponse]:
    """List all metrics records."""
    try:
        repository = MetricsRepository(db)
        return repository.get_all()
    except Exception as e:
        logger.error(f"Error listing metrics: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error listing metrics: {str(e)}",
                "trace": traceback.format_exc()
            }
        )

@metrics_router.post("/", response_model=MetricsResponse, status_code=status.HTTP_201_CREATED)
def create_metrics(
    metrics_data: MetricsCreate,
    db: Session = Depends(get_db),
):
    """Create a new metrics record."""
    try:
        logger.info(f"Creating metrics record for validation_id: {metrics_data.validation_id}")
        metrics_service = MetricsService(db)
        metrics = metrics_service.create(metrics_data)
        logger.info(f"Successfully created metrics record with ID: {metrics.id}")
        return metrics
    except ValueError as e:
        logger.error(f"Invalid data for metrics creation: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating metrics: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while creating metrics")

@metrics_router.get("/validation/{validation_id}", response_model=MetricsResponse)
def get_metrics_by_validation(
    validation_id: str,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Get metrics by validation ID."""
    try:
        repository = MetricsRepository(db)
        metrics = repository.get_by_validation_id(validation_id)
        if not metrics:
            raise ResourceNotFound("Metrics", f"for validation {validation_id}")
        return metrics
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving metrics for validation {validation_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error retrieving metrics for validation {validation_id}: {str(e)}",
                "trace": traceback.format_exc()
            }
        )

@metrics_router.get("/task/{task_id}", response_model=List[MetricsResponse])
def get_metrics_by_task(
    task_id: str,
    db: Session = Depends(get_db)
) -> List[MetricsResponse]:
    """Get all metrics for a task."""
    try:
        repository = MetricsRepository(db)
        return repository.get_by_task_id(task_id)
    except Exception as e:
        logger.error(f"Error retrieving metrics for task {task_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error retrieving metrics for task {task_id}: {str(e)}",
                "trace": traceback.format_exc()
            }
        )

@metrics_router.get("/task/{task_id}/summary")
def get_task_metrics_summary(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get summary metrics for a task."""
    try:
        repository = MetricsRepository(db)
        return repository.get_task_metrics_summary(task_id)
    except Exception as e:
        logger.error(f"Error retrieving metrics summary for task {task_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error retrieving metrics summary for task {task_id}: {str(e)}",
                "trace": traceback.format_exc()
            }
        )

@metrics_router.get("/{metrics_id}", response_model=MetricsResponse)
def get_metrics(
    metrics_id: str,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Get metrics by ID."""
    try:
        repository = MetricsRepository(db)
        metrics = repository.get_by_id(metrics_id)
        if not metrics:
            raise ResourceNotFound("Metrics", metrics_id)
        return metrics
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving metrics {metrics_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error retrieving metrics {metrics_id}: {str(e)}",
                "trace": traceback.format_exc()
            }
        )

@metrics_router.patch("/{metrics_id}", response_model=MetricsResponse)
def update_metrics(
    metrics_id: str,
    metrics_update: MetricsUpdate,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Update metrics record."""
    try:
        repository = MetricsRepository(db)
        update_data = metrics_update.model_dump(exclude_unset=True)
        metrics = repository.update(metrics_id, update_data)
        if not metrics:
            raise ResourceNotFound("Metrics", metrics_id)
        return metrics
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating metrics {metrics_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error updating metrics {metrics_id}: {str(e)}",
                "trace": traceback.format_exc()
            }
        )

@metrics_router.delete("/{metrics_id}", status_code=204)
def delete_metrics(
    metrics_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete metrics record."""
    try:
        repository = MetricsRepository(db)
        if not repository.delete(metrics_id):
            raise ResourceNotFound("Metrics", metrics_id)
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting metrics {metrics_id}: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal Server Error",
                "message": f"Error deleting metrics {metrics_id}: {str(e)}",
                "trace": traceback.format_exc()
            }
        )
