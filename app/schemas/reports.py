from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.models.reports import ReportType, ReportStatus

class ReportBase(BaseModel):
    name: str
    report_type: ReportType
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    filters: Dict[str, Any] = Field(default_factory=dict)

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[ReportStatus] = None
    content: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None

class ReportInDB(ReportBase):
    id: str
    status: ReportStatus
    content: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReportResponse(ReportInDB):
    pass 