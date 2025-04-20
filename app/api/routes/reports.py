from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.report_service import ReportService
from app.schemas.report import QualityReportCreate, QualityReportResponse, ReportStatus, ReportType
from app.api.deps import get_report_service
from app.core.exceptions import ResourceNotFound

router = APIRouter(prefix="/quality", tags=["reports"])

@router.post("/reports", response_model=QualityReportResponse)
async def create_report(report: QualityReportCreate, service: ReportService = Depends(get_report_service)) -> Any:
    """
    Submit a quality issue report.
    
    This endpoint allows users to report potential quality issues for manual review.
    """
    try:
        result = await service.create_report(report)
        return result
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@router.get("/reports/{report_id}", response_model=QualityReportResponse)
async def get_report(report_id: str, service: ReportService = Depends(get_report_service)) -> Any:
    """
    Get a report by ID.
    """
    try:
        result = await service.get_report(report_id)
        return result
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@router.get("/reports", response_model=List[QualityReportResponse])
async def list_reports(
    publisher_id: Optional[str] = None,
    task_id: Optional[str] = None,
    service: ReportService = Depends(get_report_service)
) -> Any:
    """
    List quality reports, optionally filtered by publisher or task.
    """
    try:
        result = await service.list_reports(publisher_id, task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@router.patch("/reports/{report_id}/status", response_model=QualityReportResponse)
async def update_report_status(
    report_id: str,
    status: ReportStatus,
    service: ReportService = Depends(get_report_service)
) -> Any:
    """
    Update the status of a report.
    """
    try:
        result = await service.update_report_status(report_id, status)
        return result
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })
