from typing import Dict, Any, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

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

class QualityReportBase(BaseModel):
    publisher_id: str
    session_id: str
    task_id: str
    report_type: ReportType
    details: str
    reported_at: datetime

class QualityReportCreate(QualityReportBase):
    pass

class QualityReportResponse(QualityReportBase):
    report_id: str
    status: ReportStatus = ReportStatus.RECEIVED
    estimated_review_time: str = "24 hours"

    class Config:
        orm_mode = True
