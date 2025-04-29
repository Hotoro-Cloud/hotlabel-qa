"""
Metrics service for quality assurance metrics.

This service calculates and provides metrics about quality assurance validations.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from app.db.repositories.validation_repository import ValidationRepository
from app.models.validation import Validation
from app.schemas.metrics import ValidationMetricsRequest, QualityMetricsResponse
from app.db.repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)

class MetricsService:
    """Service for calculating and providing quality assurance metrics."""
    
    def __init__(self, validation_repository):
        """
        Initialize the metrics service.
        
        Args:
            validation_repository: Repository for validation data access or db session
        """
        self.validation_repository = validation_repository
        # Check if validation_repository is a Session object
        if hasattr(validation_repository, 'query'):
            # It's a Session object
            self.db = validation_repository
            self.is_session = True
        else:
            # It's a ValidationRepository object
            self.db = validation_repository.db
            self.is_session = False
    
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
        quality_scores = [v.confidence_score for v in validations if v.confidence_score is not None]
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
                "average_quality_score": sum(v.confidence_score or 0 for v in validations) / len(validations)
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
        times = []
        for v in validations:
            if hasattr(v, 'time_spent_ms') and v.time_spent_ms is not None:
                times.append(v.time_spent_ms)
        return int(sum(times) / len(times)) if times else 0
        
    async def calculate_validation_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for validations."""
        # Get all validations
        if self.is_session:
            validations = self.db.query(Validation).all()
        else:
            validations = self.validation_repository.list({})
        
        # Calculate metrics
        total_validations = len(validations)
        if total_validations == 0:
            return {
                "total_validations": 0,
                "average_quality_score": 0.0
            }
            
        # Calculate average quality score
        quality_scores = [v.confidence_score for v in validations if v.confidence_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "total_validations": total_validations,
            "average_quality_score": avg_quality,
            "status_distribution": self._calculate_status_distribution(validations)
        }
        
    async def calculate_validator_metrics(self) -> Dict[str, Any]:
        """Calculate metrics for validators."""
        # Get all validations
        if self.is_session:
            validations = self.db.query(Validation).all()
        else:
            validations = self.validation_repository.list({})
        
        # Group by validator
        validators = {}
        for validation in validations:
            validator_id = validation.validator_id
            if validator_id not in validators:
                validators[validator_id] = {
                    "total_validations": 0,
                    "sum_quality": 0.0,
                    "validations": []
                }
                
            validators[validator_id]["total_validations"] += 1
            if validation.confidence_score is not None:
                validators[validator_id]["sum_quality"] += validation.confidence_score
            validators[validator_id]["validations"].append(validation)
            
        # Calculate metrics for each validator
        result = {}
        for validator_id, data in validators.items():
            avg_quality = data["sum_quality"] / data["total_validations"] if data["total_validations"] > 0 else 0.0
            result[validator_id] = {
                "total_validations": data["total_validations"],
                "average_quality_score": avg_quality,
                "status_distribution": self._calculate_status_distribution(data["validations"])
            }
            
        return result
        
    async def calculate_quality_metrics(self) -> Dict[str, Any]:
        """Calculate overall quality metrics."""
        validation_metrics = await self.calculate_validation_metrics()
        validator_metrics = await self.calculate_validator_metrics()
        
        return {
            "validation_metrics": validation_metrics,
            "validator_metrics": validator_metrics,
            "overall_quality_score": validation_metrics.get("average_quality_score", 0.0)
        }
        
    def _calculate_status_distribution(self, validations: List) -> Dict[str, int]:
        """Calculate distribution of validation statuses."""
        distribution = {}
        for validation in validations:
            status = validation.status.value if hasattr(validation.status, 'value') else str(validation.status)
            distribution[status] = distribution.get(status, 0) + 1
            
        return distribution
    
    async def get_metrics(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific time range.
        
        Args:
            start_date: Start date for metrics calculation
            end_date: End date for metrics calculation
            
        Returns:
            Dict: Metrics data
            
        Raises:
            ValidationError: If the time range is invalid
        """
        # Validate time range
        if start_date and end_date and start_date > end_date:
            from app.core.exceptions import ValidationError
            raise ValidationError("Start date cannot be after end date", "time_range")
            
        # Get validations for the time range
        if self.is_session:
            query = self.db.query(Validation)
            if start_date:
                query = query.filter(Validation.created_at >= start_date)
            if end_date:
                query = query.filter(Validation.created_at <= end_date)
            validations = query.all()
        else:
            validations = self.validation_repository.get_by_date_range(
                start_date=start_date,
                end_date=end_date
            )
        
        # Calculate metrics
        total_validations = len(validations)
        if total_validations == 0:
            return {
                "period": {
                    "start": start_date or datetime.utcnow(),
                    "end": end_date or datetime.utcnow()
                },
                "metrics": {
                    "total_labels": 0,
                    "average_quality_score": 0.0
                }
            }
            
        # Calculate average quality score
        quality_scores = [v.confidence_score for v in validations if v.confidence_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
        
        return {
            "period": {
                "start": start_date or min(v.created_at for v in validations),
                "end": end_date or max(v.created_at for v in validations)
            },
            "metrics": {
                "total_labels": total_validations,
                "average_quality_score": avg_quality,
                "golden_set_accuracy": self._calculate_golden_set_accuracy(validations),
                "consensus_rate": self._calculate_consensus_rate(validations),
                "suspicious_activity_percentage": self._calculate_suspicious_activity(validations),
                "average_time_per_task_ms": self._calculate_average_time(validations)
            }
        }

    def create(self, metrics_data):
        """
        Create a new metrics record
        
        Args:
            metrics_data: MetricsCreate schema with metrics data
            
        Returns:
            MetricsResponse: The created metrics record
            
        Raises:
            ValueError: If the metrics data is invalid
        """
        try:
            self.logger.info(f"Creating metrics record with validation_id: {metrics_data.validation_id}")
            
            # Create a new metrics repository
            repository = MetricsRepository(self.db)
            
            # Create the metrics record
            metrics = repository.create(metrics_data)
            
            self.logger.info(f"Successfully created metrics record with ID: {metrics.id}")
            return metrics
        except Exception as e:
            self.logger.error(f"Error creating metrics record: {str(e)}")
            raise ValueError(f"Failed to create metrics record: {str(e)}")
