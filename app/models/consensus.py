from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import Column, String, Float, Integer, DateTime, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship

from app.db.base import Base

class ConsensusStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW = "review"
    REACHED = "reached"
    FAILED = "failed"

class Consensus(Base):
    """Consensus model for storing consensus results."""
    __tablename__ = "consensus"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False)
    status = Column(SQLAlchemyEnum(ConsensusStatus), default=ConsensusStatus.PENDING)
    agreement_score = Column(Float, default=0.0)
    validator_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    validations = relationship("Validation", back_populates="consensus")
