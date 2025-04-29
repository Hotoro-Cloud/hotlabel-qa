from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from app.models.validation import ValidationStatus, ValidationMethod, ConfidenceLevel

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
    validator_id: str
    
# Model for creating a new validation
class ValidationCreate(ValidationBase):
    status: ValidationStatus = ValidationStatus.PENDING
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
    metadata: Optional[Dict[str, Any]] = None

# Request model for validation
class ValidationRequest(BaseModel):
    task_id: str
    result_id: Optional[str] = None
    session_id: Optional[str] = None
    publisher_id: Optional[str] = None
    validator_id: Optional[str] = None
    task_type: Optional[str] = None
    response: Optional[Dict[str, Any]] = None
    time_spent_ms: Optional[int] = None

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
    
    class Config:
        from_attributes = True

class ValidationUpdate(BaseModel):
    status: Optional[ValidationStatus] = None
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_level: Optional[ConfidenceLevel] = None
    issues_detected: Optional[List[Dict[str, Any]]] = None
    feedback: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ValidationInDB(ValidationBase):
    id: str
    status: ValidationStatus
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
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ValidationResponse(ValidationInDB):
    pass
