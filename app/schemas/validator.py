from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class ValidatorBase(BaseModel):
    name: str
    email: EmailStr
    is_active: bool = True

class ValidatorCreate(ValidatorBase):
    pass

class ValidatorUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None

class ValidatorResponse(ValidatorBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True 