from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base

class Task(Base):
    """Task model for storing tasks."""
    __tablename__ = "qa_tasks"

    id = Column(String(36), primary_key=True)
    type = Column(String(50), nullable=False)
    content = Column(JSON, nullable=False)
    status = Column(String(20), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    validations = relationship("Validation", back_populates="task") 