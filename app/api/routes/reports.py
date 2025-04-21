from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.reports_repository import ReportsRepository
from app.schemas.reports import ReportCreate, ReportUpdate, ReportResponse
from app.models.reports import ReportType, ReportStatus
from app.core.exceptions import ResourceNotFound

reports_router = APIRouter(prefix="/api/v1/reports", tags=["reports"])

@reports_router.post("/", response_model=ReportResponse)
def create_report(
    report_create: ReportCreate,
    db: Session = Depends(get_db)
) -> ReportResponse:
    """Create a new report."""
    repository = ReportsRepository(db)
    return repository.create(report_create)

@reports_router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    db: Session = Depends(get_db)
) -> ReportResponse:
    """Get report by ID."""
    repository = ReportsRepository(db)
    report = repository.get_by_id(report_id)
    if not report:
        raise ResourceNotFound("Report", report_id)
    return report

@reports_router.get("/", response_model=List[ReportResponse])
def list_reports(
    report_type: Optional[ReportType] = None,
    status: Optional[ReportStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
) -> List[ReportResponse]:
    """List reports with optional filters."""
    repository = ReportsRepository(db)
    return repository.list_reports(report_type, status, skip, limit)

@reports_router.patch("/{report_id}", response_model=ReportResponse)
def update_report(
    report_id: str,
    report_update: ReportUpdate,
    db: Session = Depends(get_db)
) -> ReportResponse:
    """Update report."""
    repository = ReportsRepository(db)
    update_data = report_update.model_dump(exclude_unset=True)
    report = repository.update(report_id, update_data)
    if not report:
        raise ResourceNotFound("Report", report_id)
    return report

@reports_router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete report."""
    repository = ReportsRepository(db)
    if not repository.delete(report_id):
        raise ResourceNotFound("Report", report_id)

@reports_router.get("/date-range/", response_model=List[ReportResponse])
def get_reports_by_date_range(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    report_type: Optional[ReportType] = None,
    db: Session = Depends(get_db)
) -> List[ReportResponse]:
    """Get reports within a date range."""
    repository = ReportsRepository(db)
    return repository.get_reports_by_date_range(start_date, end_date, report_type)
