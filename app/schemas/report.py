from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from app.models.reports import ReportType, ReportStatus

class ReportType(str, Enum):
    AMBIGUOUS_QUESTION = "ambiguous_question"
    INCORRECT_ANSWER = "incorrect_answer"
    MISSING_CONTEXT = "missing_context"
    TECHNICAL_ISSUE = "technical_issue"
    OTHER = "other"

class ReportStatus(str, Enum):
    RECEIVED = "received"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class ReportBase(BaseModel):
    name: str
    report_type: ReportType
    start_date: datetime
    end_date: datetime
    filters: Dict[str, List[str]]

class ReportCreate(ReportBase):
    pass

class ReportUpdate(BaseModel):
    status: Optional[ReportStatus] = None
    content: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    completed_at: Optional[datetime] = None

class ReportResponse(ReportBase):
    id: str
    status: ReportStatus
    content: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
