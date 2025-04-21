from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

class Metrics(Base):
    __tablename__ = "metrics"

    id = Column(String(36), primary_key=True)
    validation_id = Column(String(36), ForeignKey("validations.id"), nullable=False)
    task_id = Column(String(36), nullable=False, index=True)
    report_id = Column(String, ForeignKey("reports.id"), nullable=True)
    
    # Metric values
    accuracy = Column(Float, nullable=False, default=0.0)
    precision = Column(Float, nullable=False, default=0.0)
    recall = Column(Float, nullable=False, default=0.0)
    f1_score = Column(Float, nullable=False, default=0.0)
    latency_ms = Column(Integer, nullable=True)
    
    # Additional metrics
    custom_metrics = Column(JSON, default=dict)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    validation = relationship("Validation", back_populates="metrics")
    report = relationship("Report", back_populates="metrics")
