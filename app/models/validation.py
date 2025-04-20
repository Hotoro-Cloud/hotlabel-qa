import enum
from sqlalchemy import Boolean, Column, String, Integer, DateTime, Float, JSON, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

class ValidationMethod(enum.Enum):
    GOLDEN_SET = "golden_set"
    CONSENSUS = "consensus"
    STATISTICAL = "statistical"
    BOT_DETECTION = "bot_detection"
    THRESHOLD = "threshold"
    MANUAL = "manual"

class ValidationStatus(enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"

class Validation(Base):
    __tablename__ = "validations"

    id = Column(String, primary_key=True, index=True, default=lambda: f"val_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, index=True)
    result_id = Column(String, index=True)
    session_id = Column(String, index=True)
    publisher_id = Column(String, index=True)
    
    # Validation details
    validation_method = Column(Enum(ValidationMethod), nullable=False)
    status = Column(Enum(ValidationStatus), default=ValidationStatus.PENDING)
    quality_score = Column(Float, default=0.0)
    confidence = Column(Float, default=0.0)
    
    # Issues detected
    issues_detected = Column(JSON, default=list)
    feedback = Column(String, nullable=True)
    
    # Result content
    task_type = Column(String, index=True)
    response = Column(JSON, default=dict)
    time_spent_ms = Column(Integer, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    quality_metrics = relationship("QualityMetric", back_populates="validation")
    golden_set_validation = relationship("GoldenSet", back_populates="validation", uselist=False)
    consensus_group_id = Column(String, ForeignKey("consensus_groups.id"), nullable=True)
    consensus_group = relationship("ConsensusGroup", back_populates="validations")
