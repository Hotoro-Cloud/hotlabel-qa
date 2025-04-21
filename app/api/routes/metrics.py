from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.metrics_repository import MetricsRepository
from app.schemas.metrics import MetricsCreate, MetricsUpdate, MetricsResponse
from app.core.exceptions import ResourceNotFound

metrics_router = APIRouter(prefix="/api/v1/metrics", tags=["metrics"])

@metrics_router.post("/", response_model=MetricsResponse)
def create_metrics(
    metrics_create: MetricsCreate,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Create a new metrics record."""
    repository = MetricsRepository(db)
    return repository.create(metrics_create)

@metrics_router.get("/{metrics_id}", response_model=MetricsResponse)
def get_metrics(
    metrics_id: str,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Get metrics by ID."""
    repository = MetricsRepository(db)
    metrics = repository.get_by_id(metrics_id)
    if not metrics:
        raise ResourceNotFound("Metrics", metrics_id)
    return metrics

@metrics_router.get("/validation/{validation_id}", response_model=MetricsResponse)
def get_metrics_by_validation(
    validation_id: str,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Get metrics by validation ID."""
    repository = MetricsRepository(db)
    metrics = repository.get_by_validation_id(validation_id)
    if not metrics:
        raise ResourceNotFound("Metrics", f"for validation {validation_id}")
    return metrics

@metrics_router.get("/task/{task_id}", response_model=List[MetricsResponse])
def get_metrics_by_task(
    task_id: str,
    db: Session = Depends(get_db)
) -> List[MetricsResponse]:
    """Get all metrics for a task."""
    repository = MetricsRepository(db)
    return repository.get_by_task_id(task_id)

@metrics_router.patch("/{metrics_id}", response_model=MetricsResponse)
def update_metrics(
    metrics_id: str,
    metrics_update: MetricsUpdate,
    db: Session = Depends(get_db)
) -> MetricsResponse:
    """Update metrics record."""
    repository = MetricsRepository(db)
    update_data = metrics_update.model_dump(exclude_unset=True)
    metrics = repository.update(metrics_id, update_data)
    if not metrics:
        raise ResourceNotFound("Metrics", metrics_id)
    return metrics

@metrics_router.delete("/{metrics_id}", status_code=204)
def delete_metrics(
    metrics_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete metrics record."""
    repository = MetricsRepository(db)
    if not repository.delete(metrics_id):
        raise ResourceNotFound("Metrics", metrics_id)

@metrics_router.get("/task/{task_id}/summary")
def get_task_metrics_summary(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get summary metrics for a task."""
    repository = MetricsRepository(db)
    return repository.get_task_metrics_summary(task_id)
