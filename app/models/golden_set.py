from sqlalchemy import Boolean, Column, String, Integer, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

class GoldenSet(Base):
    __tablename__ = "golden_sets"

    id = Column(String, primary_key=True, index=True, default=lambda: f"gs_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, unique=True, index=True, nullable=False)
    validation_id = Column(String, ForeignKey("validations.id"), nullable=True)
    
    # Golden set data
    expected_response = Column(JSON, nullable=False)
    allowed_variation = Column(Float, default=0.0)  # Acceptable deviation from expected response
    hints = Column(JSON, default=list)  # Potential hints for difficult tasks
    
    # Metadata
    difficulty_level = Column(Integer, default=1)  # 1-5 scale of difficulty
    category = Column(String, index=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    validation = relationship("Validation", back_populates="golden_set_validation")
