from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid

from app.models.validator import Validator
from app.schemas.validator import ValidatorCreate, ValidatorUpdate

class ValidatorRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all(self) -> List[Validator]:
        """Get all validators."""
        return self.db.query(Validator).all()
    
    def get_by_id(self, validator_id: str) -> Optional[Validator]:
        """Get validator by ID."""
        return self.db.query(Validator).filter(Validator.id == validator_id).first()
    
    def get_by_email(self, email: str) -> Optional[Validator]:
        """Get validator by email."""
        return self.db.query(Validator).filter(Validator.email == email).first()
    
    def create(self, validator_data: ValidatorCreate) -> Validator:
        """Create a new validator."""
        validator_id = str(uuid.uuid4())
        db_validator = Validator(
            id=validator_id,
            name=validator_data.name,
            email=validator_data.email,
            is_active=validator_data.is_active
        )
        self.db.add(db_validator)
        self.db.commit()
        self.db.refresh(db_validator)
        return db_validator
    
    def update(self, validator_id: str, update_data: Dict[str, Any]) -> Optional[Validator]:
        """Update validator."""
        db_validator = self.get_by_id(validator_id)
        if not db_validator:
            return None
        
        for key, value in update_data.items():
            setattr(db_validator, key, value)
        
        self.db.commit()
        self.db.refresh(db_validator)
        return db_validator
    
    def delete(self, validator_id: str) -> bool:
        """Delete validator."""
        db_validator = self.get_by_id(validator_id)
        if not db_validator:
            return False
        
        self.db.delete(db_validator)
        self.db.commit()
        return True 