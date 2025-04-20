from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

# Enums that match the database models
class ValidationMethod(str, Enum):
    GOLDEN_SET = "golden_set"
    CONSENSUS = "consensus"
    STATISTICAL = "statistical"
    BOT_DETECTION = "bot_detection"
    THRESHOLD = "threshold"
    MANUAL = "manual"

class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# Base model with shared attributes
class ValidationBase(BaseModel):
    task_id: str
    result_id: str
    session_id: str
    publisher_id: str
    task_type: str
    response: Dict[str, Any]
    time_spent_ms: Optional[int] = None

# Model for creating a new validation
class ValidationCreate(ValidationBase):
    validation_method: ValidationMethod
    
# Request model for validation
class ValidationRequest(BaseModel):
    task_id: str
    session_id: str
    publisher_id: str
    response: Any
    time_spent_ms: int
    task_type: str
    validation_type: Optional[ValidationMethod] = None

# Response model for validation result
class ValidationResponse(ValidationBase):
    id: str
    validation_method: ValidationMethod
    status: ValidationStatus
    quality_score: float
    confidence: float
    confidence_level: ConfidenceLevel = Field(...)
    issues_detected: List[Dict[str, Any]] = []
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @property
    def confidence_level(self) -> ConfidenceLevel:
        # This would normally be a method in the schema, but I'm showing it as a computed field
        from app.core.config import settings
        
        if self.confidence >= settings.HIGH_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.HIGH
        elif self.confidence >= settings.MEDIUM_CONFIDENCE_THRESHOLD:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW
    
    class Config:
        orm_mode = True
