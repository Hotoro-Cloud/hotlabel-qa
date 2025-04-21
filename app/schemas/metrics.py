from typing import Dict, Any, List, Optional
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel, Field

class GranularityType(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class ValidationMetricsRequest(BaseModel):
    publisher_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    task_type: Optional[str] = None
    granularity: GranularityType = GranularityType.DAILY

class TimeSeriesPoint(BaseModel):
    date: date
    total_labels: int
    average_quality_score: float

class TaskTypeMetrics(BaseModel):
    total_labels: int
    average_quality_score: float

class QualityMetricsResponse(BaseModel):
    period: Dict[str, datetime]
    metrics: Dict[str, Any]
    breakdown_by_task_type: Dict[str, TaskTypeMetrics]
    time_series: List[TimeSeriesPoint]

class MetricsBase(BaseModel):
    validation_id: str
    task_id: str
    accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    precision: float = Field(default=0.0, ge=0.0, le=1.0)
    recall: float = Field(default=0.0, ge=0.0, le=1.0)
    f1_score: float = Field(default=0.0, ge=0.0, le=1.0)
    latency_ms: Optional[int] = None
    custom_metrics: Dict[str, Any] = Field(default_factory=dict)

class MetricsCreate(MetricsBase):
    pass

class MetricsUpdate(BaseModel):
    accuracy: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    precision: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    recall: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    f1_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    latency_ms: Optional[int] = None
    custom_metrics: Optional[Dict[str, Any]] = None

class MetricsInDB(MetricsBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class MetricsResponse(MetricsInDB):
    pass
