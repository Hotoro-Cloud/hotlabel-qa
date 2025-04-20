from typing import Dict, Any, List, Tuple, Optional
import logging
import statistics
from datetime import datetime, timedelta

from app.services.validators.base_validator import BaseValidator
from app.db.repositories.validation_repository import ValidationRepository

logger = logging.getLogger(__name__)

class StatisticalValidator(BaseValidator):
    """Validator that uses statistical methods to assess responses"""
    
    def __init__(self, validation_repository: ValidationRepository):
        self.validation_repository = validation_repository
    
    async def validate(self, task_id: str, response: Any, session_id: str, **kwargs) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        publisher_id = kwargs.get('publisher_id', '')
        task_type = kwargs.get('task_type', '')
        time_spent_ms = kwargs.get('time_spent_ms', 0)
        
        issues = []
        
        # Get recent validations for this task across all users
        # In a real implementation, this would be more optimized with caching
        # and database queries would be more targeted
        now = datetime.now()
        start_date = now - timedelta(days=7)  # Look at data from last 7 days
        
        similar_validations = self.validation_repository.get_by_publisher_and_date_range(
            publisher_id=publisher_id,
            start_date=start_date,
            end_date=now
        )
        
        # Filter to only include validations for this task type
        similar_validations = [v for v in similar_validations if v.task_type == task_type]
        
        if not similar_validations:
            logger.info(f"No statistical baseline available for task type {task_type}")
            # Without statistical data, we can't make a good assessment
            return 0.5, 0.3, [], None
        
        # Calculate statistical metrics from past validations
        # 1. Response time analysis
        time_quality = self._analyze_response_time(time_spent_ms, similar_validations)
        
        # 2. Response content analysis - compare with distributions of past responses
        # This is highly domain-specific and would be implemented differently for different task types
        content_quality = self._analyze_content(response, similar_validations, task_type)
        
        # 3. Look for statistical outliers
        outlier_analysis = self._check_for_outliers(response, time_spent_ms, similar_validations)
        
        # Combine the analyses, weighted as appropriate
        quality_score = (time_quality[0] * 0.3) + (content_quality[0] * 0.5) + (outlier_analysis[0] * 0.2)
        confidence = (time_quality[1] * 0.3) + (content_quality[1] * 0.5) + (outlier_analysis[1] * 0.2)
        
        # Collect issues from all analyses
        issues.extend(time_quality[2])
        issues.extend(content_quality[2])
        issues.extend(outlier_analysis[2])
        
        feedback = None
        if issues:
            feedback = "Your response significantly differs from typical patterns."
        
        return quality_score, confidence, issues, feedback
    
    def _analyze_response_time(self, time_spent_ms: int, similar_validations: List) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Analyze response time compared to statistical baseline"""
        issues = []
        
        # Extract response times from similar validations
        response_times = [v.time_spent_ms for v in similar_validations if v.time_spent_ms is not None]
        
        if not response_times:
            return 0.5, 0.3, []  # No baseline, return neutral score with low confidence
        
        # Calculate statistics
        try:
            mean_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            stdev = statistics.stdev(response_times) if len(response_times) > 1 else mean_time * 0.5
        except Exception as e:
            logger.error(f"Error calculating time statistics: {str(e)}")
            return 0.5, 0.3, []
        
        # Z-score of current response time
        if stdev > 0:
            z_score = (time_spent_ms - mean_time) / stdev
        else:
            z_score = 0 if time_spent_ms == mean_time else float('inf') * (1 if time_spent_ms > mean_time else -1)
        
        # Quality score based on deviation from norm
        # Extremely fast or slow responses get lower quality scores
        if abs(z_score) > 3:  # More than 3 standard deviations away
            quality_score = 0.3
            confidence = 0.8
            issues.append({
                "type": "unusual_response_time",
                "message": "Response time is unusual compared to typical responses",
                "z_score": z_score,
                "time_spent_ms": time_spent_ms,
                "mean_time_ms": mean_time
            })
        elif abs(z_score) > 2:  # 2-3 standard deviations away
            quality_score = 0.5
            confidence = 0.7
        elif abs(z_score) > 1:  # 1-2 standard deviations away
            quality_score = 0.7
            confidence = 0.6
        else:  # Within 1 standard deviation (normal)
            quality_score = 0.9
            confidence = 0.8
        
        return quality_score, confidence, issues
    
    def _analyze_content(self, response: Any, similar_validations: List, task_type: str) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Analyze response content compared to statistical baseline"""
        # This is highly dependent on the response type and would be customized
        # for different task types in a real implementation
        
        issues = []
        
        if task_type == "multiple_choice" and isinstance(response, str):
            return self._analyze_multiple_choice(response, similar_validations)
        elif task_type == "open_text" and isinstance(response, str):
            return self._analyze_open_text(response, similar_validations)
        else:
            # Default simple analysis for other types
            return 0.7, 0.5, []
    
    def _analyze_multiple_choice(self, response: str, similar_validations: List) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Analyze multiple choice response"""
        issues = []
        
        # Extract previous responses
        previous_responses = [v.response for v in similar_validations if isinstance(v.response, str)]
        
        if not previous_responses:
            return 0.5, 0.3, []  # No baseline, return neutral score with low confidence
        
        # Count frequency of each response
        from collections import Counter
        response_counts = Counter(previous_responses)
        total_responses = len(previous_responses)
        
        # Calculate frequency of the current response
        response_frequency = response_counts.get(response, 0) / total_responses if total_responses > 0 else 0
        
        # Quality score based on how common this response is
        if response_frequency == 0:  # Never seen before
            quality_score = 0.4
            confidence = 0.6
            issues.append({
                "type": "unusual_response",
                "message": "This response has not been observed in similar tasks"
            })
        elif response_frequency < 0.1:  # Rare response (< 10%)
            quality_score = 0.6
            confidence = 0.7
        else:  # Common response
            quality_score = 0.8
            confidence = 0.8
        
        return quality_score, confidence, issues
    
    def _analyze_open_text(self, response: str, similar_validations: List) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Analyze open text response"""
        # This would be a complex implementation in a real system
        # For now, we'll return a default score with medium confidence
        return 0.7, 0.5, []
    
    def _check_for_outliers(self, response: Any, time_spent_ms: int, similar_validations: List) -> Tuple[float, float, List[Dict[str, Any]]]:
        """Check if the response is a statistical outlier in any dimension"""
        # This would involve more sophisticated analysis in a real system
        # For now, we'll do a simple check on response content length
        
        issues = []
        
        if isinstance(response, str):
            # Check if response length is unusual
            response_lengths = [len(str(v.response)) for v in similar_validations 
                               if v.response is not None and isinstance(v.response, str)]
            
            if response_lengths:
                try:
                    mean_length = statistics.mean(response_lengths)
                    stdev = statistics.stdev(response_lengths) if len(response_lengths) > 1 else mean_length * 0.5
                    
                    current_length = len(response)
                    if stdev > 0:
                        z_score = (current_length - mean_length) / stdev
                    else:
                        z_score = 0 if current_length == mean_length else float('inf') * (1 if current_length > mean_length else -1)
                    
                    if abs(z_score) > 3:  # More than 3 standard deviations away
                        quality_score = 0.4
                        confidence = 0.7
                        issues.append({
                            "type": "unusual_response_length",
                            "message": "Response length is unusually different from typical responses",
                            "z_score": z_score,
                            "length": current_length,
                            "mean_length": mean_length
                        })
                    elif abs(z_score) > 2:  # 2-3 standard deviations away
                        quality_score = 0.6
                        confidence = 0.6
                    else:  # Within 2 standard deviations (normal)
                        quality_score = 0.8
                        confidence = 0.7
                    
                    return quality_score, confidence, issues
                    
                except Exception as e:
                    logger.error(f"Error checking for outliers: {str(e)}")
        
        # Default if we can't perform outlier analysis
        return 0.7, 0.4, []
