import enum
from sqlalchemy import Boolean, Column, String, Integer, DateTime, Float, JSON, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from datetime import datetime

from app.db.base import Base
from app.models.consensus import ConsensusStatus

class ValidationMethod(enum.Enum):
    GOLDEN_SET = "golden_set"
    CONSENSUS = "consensus"
    STATISTICAL = "statistical"
    BOT_DETECTION = "bot_detection"
    THRESHOLD = "threshold"
    MANUAL = "manual"

class ValidationStatus(str, enum.Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    APPROVED = "approved"  # For backward compatibility
    REJECTED = "rejected"
    NEEDS_REVIEW = "needs_review"
    REVIEW = "review"  # For backward compatibility

class Validation(Base):
    __tablename__ = "validations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False)
    validator_id = Column(String(36), ForeignKey("validators.id"), nullable=False)
    consensus_id = Column(String(36), ForeignKey("consensus.id"), nullable=True)
    status = Column(Enum(ValidationStatus), nullable=False)
    confidence_score = Column(Float, nullable=True)
    validation_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = relationship("Task", back_populates="validations")
    validator = relationship("Validator", back_populates="validations")
    consensus = relationship("Consensus", back_populates="validations")
    metrics = relationship("Metrics", back_populates="validation", uselist=False)
    golden_set_validation = relationship("GoldenSet", back_populates="validation", uselist=False)
