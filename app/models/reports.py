from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Integer, DateTime, JSON, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

class ReportType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class ReportStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"

class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, index=True, default=lambda: f"rep_{uuid.uuid4().hex[:8]}")
    name = Column(String, nullable=False)
    report_type = Column(SQLAlchemyEnum(ReportType), nullable=False)
    status = Column(SQLAlchemyEnum(ReportStatus), nullable=False, default=ReportStatus.PENDING)
    
    # Report parameters
    start_date = Column(DateTime(timezone=True), nullable=True)
    end_date = Column(DateTime(timezone=True), nullable=True)
    filters = Column(JSON, default=dict)
    
    # Report content
    content = Column(JSON, nullable=True)
    summary = Column(JSON, nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    metrics = relationship("Metrics", back_populates="report") 