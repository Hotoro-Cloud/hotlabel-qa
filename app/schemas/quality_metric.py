from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class QualityMetricBase(BaseModel):
    validation_id: str
    quality_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    issues_detected: Dict[str, Any] = {}
    time_ms: Optional[int] = None
    metrics: Dict[str, Any] = {}

class QualityMetricCreate(QualityMetricBase):
    pass

class QualityMetricUpdate(BaseModel):
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    issues_detected: Optional[Dict[str, Any]] = None
    time_ms: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None

class QualityMetricInDB(QualityMetricBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QualityMetricResponse(QualityMetricInDB):
    pass
