from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel

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
        orm_mode = True
