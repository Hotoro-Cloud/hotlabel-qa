"""
Metrics service for quality assurance metrics.

This service calculates and provides metrics about quality assurance validations.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.db.repositories.validation_repository import ValidationRepository
from app.schemas.metrics import ValidationMetricsRequest, QualityMetricsResponse

logger = logging.getLogger(__name__)

class MetricsService:
    """Service for calculating and providing quality assurance metrics."""
    
    def __init__(self, validation_repository: ValidationRepository):
        """
        Initialize the metrics service.
        
        Args:
            validation_repository: Repository for validation data access
        """
        self.validation_repository = validation_repository
    
    async def get_publisher_metrics(
        self, request: ValidationMetricsRequest
    ) -> QualityMetricsResponse:
        """
        Get quality metrics for a publisher.
        
        Args:
            request: Metrics request parameters
            
        Returns:
            QualityMetricsResponse: Quality metrics
        """
        # Get validations based on request parameters
        validations = self.validation_repository.get_by_publisher_and_date_range(
            publisher_id=request.publisher_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Filter by task type if provided
        if request.task_type:
            validations = [v for v in validations if v.task_type == request.task_type]
        
        # Calculate metrics
        total_validations = len(validations)
        if total_validations == 0:
            return self._create_empty_metrics(request)
        
        # Calculate average quality score
        quality_scores = [v.quality_score for v in validations if v.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        # Calculate breakdown by task type
        task_types = {}
        for validation in validations:
            task_type = validation.task_type or "unknown"
            if task_type not in task_types:
                task_types[task_type] = {
                    "total_labels": 0,
                    "average_quality_score": 0.0,
                    "sum_quality": 0.0
                }
            
            task_types[task_type]["total_labels"] += 1
            if validation.quality_score is not None:
                task_types[task_type]["sum_quality"] += validation.quality_score
        
        # Calculate averages for each task type
        for task_type in task_types:
            if task_types[task_type]["total_labels"] > 0 and task_types[task_type]["sum_quality"] > 0:
                task_types[task_type]["average_quality_score"] = (
                    task_types[task_type]["sum_quality"] / task_types[task_type]["total_labels"]
                )
            del task_types[task_type]["sum_quality"]
        
        # Generate time series data based on granularity
        time_series = self._generate_time_series(
            validations=validations,
            granularity=request.granularity,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Compile response
        return QualityMetricsResponse(
            period={
                "start": request.start_date or validations[0].created_at,
                "end": request.end_date or datetime.utcnow()
            },
            metrics={
                "total_labels": total_validations,
                "average_quality_score": avg_quality,
                "golden_set_accuracy": self._calculate_golden_set_accuracy(validations),
                "consensus_rate": self._calculate_consensus_rate(validations),
                "suspicious_activity_percentage": self._calculate_suspicious_activity(validations),
                "average_time_per_task_ms": self._calculate_average_time(validations)
            },
            breakdown_by_task_type=task_types,
            time_series=time_series
        )
    
    def _create_empty_metrics(self, request: ValidationMetricsRequest) -> QualityMetricsResponse:
        """Create empty metrics response when no data is available."""
        return QualityMetricsResponse(
            period={
                "start": request.start_date or datetime.utcnow(),
                "end": request.end_date or datetime.utcnow()
            },
            metrics={
                "total_labels": 0,
                "average_quality_score": 0.0,
                "golden_set_accuracy": 0.0,
                "consensus_rate": 0.0,
                "suspicious_activity_percentage": 0.0,
                "average_time_per_task_ms": 0
            },
            breakdown_by_task_type={},
            time_series=[]
        )
    
    def _generate_time_series(
        self, 
        validations: List,
        granularity: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Generate time series data based on granularity."""
        # Default implementation with placeholder data
        # In a real implementation, this would group validations by time period
        if not validations:
            return []
        
        # Use provided dates or infer from validations
        start = start_date or min(v.created_at for v in validations)
        end = end_date or max(v.created_at for v in validations)
        
        # Sample time series points
        return [
            {
                "date": start.date(),
                "total_labels": len(validations),
                "average_quality_score": sum(v.quality_score or 0 for v in validations) / len(validations)
            }
        ]
    
    def _calculate_golden_set_accuracy(self, validations: List) -> float:
        """Calculate accuracy on golden set validation tasks."""
        # Placeholder implementation
        return 0.9
    
    def _calculate_consensus_rate(self, validations: List) -> float:
        """Calculate consensus rate among validators."""
        # Placeholder implementation
        return 0.85
    
    def _calculate_suspicious_activity(self, validations: List) -> float:
        """Calculate percentage of suspicious activity."""
        # Placeholder implementation
        return 0.02
    
    def _calculate_average_time(self, validations: List) -> int:
        """Calculate average time spent on tasks."""
        times = [v.time_spent_ms for v in validations if v.time_spent_ms is not None]
        return int(sum(times) / len(times)) if times else 0