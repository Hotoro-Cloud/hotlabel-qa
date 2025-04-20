from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class QualityMetricBase(BaseModel):
    metric_type: str
    value: float
    weight: float = 1.0
    metadata: Dict[str, Any] = {}

class QualityMetricCreate(QualityMetricBase):
    validation_id: str

class QualityMetricResponse(QualityMetricBase):
    id: str
    validation_id: str
    created_at: datetime
    
    class Config:
        orm_mode = True
