from sqlalchemy import Boolean, Column, String, Integer, DateTime, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.db.base import Base

class ConsensusStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class ConsensusGroup(Base):
    __tablename__ = "consensus_groups"

    id = Column(String, primary_key=True, index=True, default=lambda: f"cg_{uuid.uuid4().hex[:8]}")
    task_id = Column(String, index=True, nullable=False)
    
    # Consensus status
    status = Column(Enum(ConsensusStatus), default=ConsensusStatus.PENDING)
    required_validations = Column(Integer, default=3)
    agreement_threshold = Column(Float, default=0.75)  # 0.75 means 75% agreement required
    
    # Results
    consensus_result = Column(JSON, nullable=True)  # Final agreed-upon result
    agreement_level = Column(Float, nullable=True)  # Actual agreement achieved
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    validations = relationship("Validation", back_populates="consensus_group")
