from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
from app.models.consensus import ConsensusStatus

class ConsensusStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ConsensusGroupBase(BaseModel):
    task_id: str
    required_validations: int = 3
    agreement_threshold: float = 0.75

class ConsensusGroupCreate(ConsensusGroupBase):
    pass

class ConsensusGroupResponse(ConsensusGroupBase):
    id: str
    status: ConsensusStatus
    consensus_result: Optional[Dict[str, Any]] = None
    agreement_level: Optional[float] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    validation_count: int = 0
    
    class Config:
        from_attributes = True

class ConsensusBase(BaseModel):
    task_id: str
    status: ConsensusStatus = Field(default=ConsensusStatus.PENDING)
    agreement_score: float = Field(default=0.0, ge=0.0, le=1.0)
    validator_count: int = Field(default=0, ge=0)

class ConsensusCreate(ConsensusBase):
    pass

class ConsensusUpdate(BaseModel):
    status: ConsensusStatus | None = None
    agreement_score: float | None = Field(default=None, ge=0.0, le=1.0)
    validator_count: int | None = Field(default=None, ge=0)

class ConsensusInDB(ConsensusBase):
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConsensusResponse(ConsensusInDB):
    pass

class ConsensusStatistics(BaseModel):
    total_count: int
    status_distribution: dict[ConsensusStatus, int]
    average_agreement_score: float

class ConsensusFilter(BaseModel):
    status: ConsensusStatus | None = None
    min_agreement_score: float | None = Field(default=None, ge=0.0, le=1.0)
    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=100, ge=1)
