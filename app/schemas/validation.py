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
    APPROVED = "approved"  # For backward compatibility
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    REVIEW = "review"  # For backward compatibility

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
class ValidationResponse(BaseModel):
    id: str
    task_id: str
    status: ValidationStatus
    validator_id: Optional[str] = None
    result_id: Optional[str] = None
    session_id: Optional[str] = None
    publisher_id: Optional[str] = None
    validation_method: Optional[ValidationMethod] = None
    task_type: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    time_spent_ms: Optional[int] = None
    quality_score: Optional[float] = None
    confidence_score: Optional[float] = None
    confidence: Optional[float] = None
    confidence_level: Optional[ConfidenceLevel] = None
    issues_detected: List[Dict[str, Any]] = []
    feedback: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Remove the property since it's now an optional field
    
    class Config:
        orm_mode = True
