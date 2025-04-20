from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.golden_set import GoldenSet
from app.schemas.golden_set import GoldenSetCreate

class GoldenSetRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, golden_set_data: GoldenSetCreate) -> GoldenSet:
        db_golden_set = GoldenSet(
            task_id=golden_set_data.task_id,
            expected_response=golden_set_data.expected_response,
            allowed_variation=golden_set_data.allowed_variation,
            hints=golden_set_data.hints,
            difficulty_level=golden_set_data.difficulty_level,
            category=golden_set_data.category,
            tags=golden_set_data.tags
        )
        self.db.add(db_golden_set)
        self.db.commit()
        self.db.refresh(db_golden_set)
        return db_golden_set
    
    def get_by_id(self, golden_set_id: str) -> Optional[GoldenSet]:
        return self.db.query(GoldenSet).filter(GoldenSet.id == golden_set_id).first()
    
    def get_by_task_id(self, task_id: str) -> Optional[GoldenSet]:
        return self.db.query(GoldenSet).filter(GoldenSet.task_id == task_id).first()
    
    def list_by_category(self, category: str) -> List[GoldenSet]:
        return self.db.query(GoldenSet).filter(GoldenSet.category == category).all()
    
    def update(self, golden_set_id: str, update_data: Dict[str, Any]) -> Optional[GoldenSet]:
        db_golden_set = self.get_by_id(golden_set_id)
        if not db_golden_set:
            return None
        
        for key, value in update_data.items():
            setattr(db_golden_set, key, value)
        
        self.db.commit()
        self.db.refresh(db_golden_set)
        return db_golden_set
    
    def link_validation(self, golden_set_id: str, validation_id: str) -> Optional[GoldenSet]:
        db_golden_set = self.get_by_id(golden_set_id)
        if not db_golden_set:
            return None
        
        db_golden_set.validation_id = validation_id
        self.db.commit()
        self.db.refresh(db_golden_set)
        return db_golden_set
    
    def get_random_golden_set(self, category: Optional[str] = None, difficulty_level: Optional[int] = None) -> Optional[GoldenSet]:
        query = self.db.query(GoldenSet)
        
        if category:
            query = query.filter(GoldenSet.category == category)
        
        if difficulty_level:
            query = query.filter(GoldenSet.difficulty_level == difficulty_level)
        
        # Use random ordering (database-specific implementation would be needed)
        # This is a simplified version using RANDOM() function
        from sqlalchemy.sql.expression import func
        return query.order_by(func.random()).first()
