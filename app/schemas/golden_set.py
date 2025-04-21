from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel

class GoldenSetBase(BaseModel):
    task_id: str
    expected_response: Dict[str, Any]
    allowed_variation: float = 0.0
    hints: List[str] = []
    difficulty_level: int = 1
    category: Optional[str] = "unknown"
    tags: List[str] = []

class GoldenSetCreate(GoldenSetBase):
    pass

class GoldenSetResponse(GoldenSetBase):
    id: str
    validation_id: Optional[str] = None
    status: Optional[str] = "pending"
    confidence_score: float = 1.0
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True
