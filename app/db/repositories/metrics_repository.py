from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.metrics import Metrics
from app.schemas.metrics import MetricsCreate, MetricsUpdate

class MetricsRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, metrics_data: MetricsCreate) -> Metrics:
        """Create a new metrics record."""
        db_metrics = Metrics(**metrics_data.model_dump())
        self.db.add(db_metrics)
        self.db.commit()
        self.db.refresh(db_metrics)
        return db_metrics
    
    def get_by_id(self, metrics_id: str) -> Optional[Metrics]:
        """Get metrics by ID."""
        return self.db.query(Metrics).filter(Metrics.id == metrics_id).first()
    
    def get_by_validation_id(self, validation_id: str) -> Optional[Metrics]:
        """Get metrics by validation ID."""
        return self.db.query(Metrics).filter(Metrics.validation_id == validation_id).first()
    
    def get_by_task_id(self, task_id: str) -> List[Metrics]:
        """Get all metrics for a task."""
        return self.db.query(Metrics).filter(Metrics.task_id == task_id).all()
    
    def update(self, metrics_id: str, update_data: Dict[str, Any]) -> Optional[Metrics]:
        """Update metrics record."""
        db_metrics = self.get_by_id(metrics_id)
        if not db_metrics:
            return None
        
        for key, value in update_data.items():
            setattr(db_metrics, key, value)
        
        self.db.commit()
        self.db.refresh(db_metrics)
        return db_metrics
    
    def delete(self, metrics_id: str) -> bool:
        """Delete metrics record."""
        db_metrics = self.get_by_id(metrics_id)
        if not db_metrics:
            return False
        
        self.db.delete(db_metrics)
        self.db.commit()
        return True
    
    def get_task_metrics_summary(self, task_id: str) -> Dict[str, Any]:
        """Get summary metrics for a task."""
        from sqlalchemy import func
        
        metrics = self.db.query(Metrics).filter(Metrics.task_id == task_id).all()
        
        if not metrics:
            return {
                "count": 0,
                "avg_accuracy": 0.0,
                "avg_precision": 0.0,
                "avg_recall": 0.0,
                "avg_f1_score": 0.0,
                "avg_latency_ms": 0
            }
        
        # Calculate averages
        total_count = len(metrics)
        avg_accuracy = sum(m.accuracy for m in metrics) / total_count
        avg_precision = sum(m.precision for m in metrics) / total_count
        avg_recall = sum(m.recall for m in metrics) / total_count
        avg_f1_score = sum(m.f1_score for m in metrics) / total_count
        
        # Calculate average latency (excluding None values)
        latencies = [m.latency_ms for m in metrics if m.latency_ms is not None]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "count": total_count,
            "avg_accuracy": avg_accuracy,
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "avg_f1_score": avg_f1_score,
            "avg_latency_ms": avg_latency
        } 