from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.validation import Validation, ValidationMethod, ValidationStatus
from app.schemas.validation import ValidationCreate

class ValidationRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, validation_data: ValidationCreate) -> Validation:
        db_validation = Validation(
            task_id=validation_data.task_id,
            result_id=validation_data.result_id,
            session_id=validation_data.session_id,
            publisher_id=validation_data.publisher_id,
            validation_method=validation_data.validation_method,
            task_type=validation_data.task_type,
            response=validation_data.response,
            time_spent_ms=validation_data.time_spent_ms
        )
        self.db.add(db_validation)
        self.db.commit()
        self.db.refresh(db_validation)
        return db_validation
    
    def get_by_id(self, validation_id: str) -> Optional[Validation]:
        return self.db.query(Validation).filter(Validation.id == validation_id).first()
    
    def get_by_task_id(self, task_id: str) -> List[Validation]:
        return self.db.query(Validation).filter(Validation.task_id == task_id).all()
    
    def get_by_result_id(self, result_id: str) -> Optional[Validation]:
        return self.db.query(Validation).filter(Validation.result_id == result_id).first()
    
    def update(self, validation_id: str, update_data: Dict[str, Any]) -> Optional[Validation]:
        db_validation = self.get_by_id(validation_id)
        if not db_validation:
            return None
        
        for key, value in update_data.items():
            setattr(db_validation, key, value)
        
        self.db.commit()
        self.db.refresh(db_validation)
        return db_validation
    
    def update_quality_score(self, validation_id: str, quality_score: float, confidence: float) -> Optional[Validation]:
        db_validation = self.get_by_id(validation_id)
        if not db_validation:
            return None
        
        db_validation.quality_score = quality_score
        db_validation.confidence = confidence
        
        # Update status based on confidence
        from app.core.config import settings
        if confidence >= settings.HIGH_CONFIDENCE_THRESHOLD:
            db_validation.status = ValidationStatus.VALIDATED
        elif confidence >= settings.MEDIUM_CONFIDENCE_THRESHOLD:
            db_validation.status = ValidationStatus.NEEDS_REVIEW
        else:
            db_validation.status = ValidationStatus.REJECTED
        
        self.db.commit()
        self.db.refresh(db_validation)
        return db_validation
    
    def get_recent_by_session(self, session_id: str, limit: int = 10) -> List[Validation]:
        return self.db.query(Validation)\
            .filter(Validation.session_id == session_id)\
            .order_by(Validation.created_at.desc())\
            .limit(limit)\
            .all()
    
    def get_by_publisher_and_date_range(self, publisher_id: str, start_date, end_date) -> List[Validation]:
        query = self.db.query(Validation).filter(Validation.publisher_id == publisher_id)
        
        if start_date:
            query = query.filter(Validation.created_at >= start_date)
        
        if end_date:
            query = query.filter(Validation.created_at <= end_date)
        
        return query.all()
        
    def get_by_date_range(self, start_date, end_date) -> List[Validation]:
        """Get validations within a date range"""
        query = self.db.query(Validation)
        
        if start_date:
            query = query.filter(Validation.created_at >= start_date)
        
        if end_date:
            query = query.filter(Validation.created_at <= end_date)
        
        return query.all()
        
    def list(self, filters: Dict[str, Any] = None) -> List[Validation]:
        """List validations with optional filters"""
        query = self.db.query(Validation)
        
        if filters:
            for key, value in filters.items():
                if hasattr(Validation, key):
                    query = query.filter(getattr(Validation, key) == value)
        
        return query.all()
        
    def delete(self, validation: Validation) -> None:
        """Delete a validation"""
        self.db.delete(validation)
        self.db.commit()
