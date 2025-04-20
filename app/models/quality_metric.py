from sqlalchemy import Boolean, Column, String, Integer, DateTime, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.db.base import Base

class QualityMetric(Base):
    __tablename__ = "quality_metrics"

    id = Column(String, primary_key=True, index=True, default=lambda: f"qm_{uuid.uuid4().hex[:8]}")
    validation_id = Column(String, ForeignKey("validations.id"), nullable=False)
    
    # Metric data
    metric_type = Column(String, nullable=False, index=True)
    value = Column(Float, nullable=False)
    weight = Column(Float, default=1.0)
    metadata = Column(JSON, default=dict)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    validation = relationship("Validation", back_populates="quality_metrics")
