from typing import Dict, Any, List, Optional
from datetime import datetime, date
from enum import Enum
from pydantic import BaseModel

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
