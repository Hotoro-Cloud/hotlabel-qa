from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.metrics_service import MetricsService
from app.schemas.metrics import ValidationMetricsRequest, QualityMetricsResponse, GranularityType
from app.api.deps import get_metrics_service

router = APIRouter(prefix="/quality", tags=["metrics"])

@router.post("/metrics", response_model=QualityMetricsResponse)
async def get_quality_metrics(request: ValidationMetricsRequest, service: MetricsService = Depends(get_metrics_service)) -> Any:
    """
    Get quality metrics for a publisher.
    
    This endpoint provides aggregated quality metrics for a publisher's labels.
    """
    try:
        result = await service.get_publisher_metrics(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })
