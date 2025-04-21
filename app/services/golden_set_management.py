from typing import Dict, Any, List, Optional, Tuple
import logging
import json
import uuid
from datetime import datetime

from app.db.repositories.golden_set_repository import GoldenSetRepository
from app.db.repositories.validation_repository import ValidationRepository
from app.schemas.golden_set import GoldenSetCreate, GoldenSetResponse, GoldenSetUpdate
from app.schemas.golden_set_analytics import GoldenSetPerformance, GoldenSetSuggestion
from app.core.exceptions import ResourceNotFound, ValidationError

logger = logging.getLogger(__name__)

class GoldenSetManagementService:
    """
    Service for managing golden sets including creation, updating, and feedback loops.
    
    This service provides mechanisms for:
    1. Creating and updating golden sets
    2. Analyzing golden set performance metrics
    3. Suggesting improvements to golden sets based on validation results
    4. Generating new golden set candidates from high-confidence validations
    """
    
    def __init__(
        self, 
        golden_set_repository: GoldenSetRepository,
        validation_repository: ValidationRepository
    ):
        self.golden_set_repository = golden_set_repository
        self.validation_repository = validation_repository
    
    async def create_golden_set(self, golden_set_data: GoldenSetCreate) -> GoldenSetResponse:
        """
        Create a new golden set item.
        
        Args:
            golden_set_data: Data for the new golden set
            
        Returns:
            The created golden set
        """
        # Validate expected_response format based on task_type
        self._validate_expected_response(golden_set_data.task_type, golden_set_data.expected_response)
        
        # Create the golden set
        golden_set = self.golden_set_repository.create(golden_set_data)
        
        logger.info(f"Created golden set {golden_set.id} for task {golden_set_data.task_id}")
        
        return GoldenSetResponse.from_orm(golden_set)
    
    async def update_golden_set(self, golden_set_id: str, update_data: GoldenSetUpdate) -> GoldenSetResponse:
        """
        Update an existing golden set item.
        
        Args:
            golden_set_id: ID of the golden set to update
            update_data: Data to update
            
        Returns:
            The updated golden set
            
        Raises:
            ResourceNotFound: If golden set is not found
        """
        # Get the current golden set
        golden_set = self.golden_set_repository.get_by_id(golden_set_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", golden_set_id)
        
        # Validate expected_response if it's being updated
        if update_data.expected_response:
            task_type = update_data.task_type or golden_set.task_type
            self._validate_expected_response(task_type, update_data.expected_response)
        
        # Update the golden set
        golden_set = self.golden_set_repository.update(golden_set_id, update_data.dict(exclude_unset=True))
        
        logger.info(f"Updated golden set {golden_set_id}")
        
        return GoldenSetResponse.from_orm(golden_set)
    
    def _validate_expected_response(self, task_type: str, expected_response: Any) -> None:
        """
        Validate that the expected response matches the format required for the task type.
        
        Args:
            task_type: Type of task (e.g., 'vqa', 'text_classification', etc.)
            expected_response: Expected response to validate
            
        Raises:
            ValidationError: If the expected response is invalid for the task type
        """
        # Define validation rules based on task_type
        if task_type == "vqa":
            # VQA responses should typically be strings or dictionaries
            if not isinstance(expected_response, (str, dict)):
                raise ValidationError(
                    f"VQA expected response should be a string or dictionary, got {type(expected_response).__name__}"
                )
        
        elif task_type == "text_classification":
            # Text classification should be a string, list of strings, or dictionary
            valid_types = (str, list, dict)
            if not isinstance(expected_response, valid_types):
                raise ValidationError(
                    f"Text classification expected response should be one of {valid_types}, "
                    f"got {type(expected_response).__name__}"
                )
                
            # If it's a list, check that it contains strings
            if isinstance(expected_response, list) and not all(isinstance(x, str) for x in expected_response):
                raise ValidationError("Text classification list response should contain only strings")
        
        # Add validation for other task types as needed
        
        # Fallback validation: just ensure it's a valid JSON-serializable type
        try:
            json.dumps(expected_response)
        except (TypeError, OverflowError):
            raise ValidationError("Expected response must be JSON-serializable")
    
    async def get_golden_set_performance(self, golden_set_id: str) -> GoldenSetPerformance:
        """
        Get performance metrics for a golden set.
        
        Args:
            golden_set_id: ID of the golden set
            
        Returns:
            Performance metrics
            
        Raises:
            ResourceNotFound: If golden set is not found
        """
        # Get the golden set
        golden_set = self.golden_set_repository.get_by_id(golden_set_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", golden_set_id)
        
        # Get validations that used this golden set
        validations = self.validation_repository.find_by_task_id(golden_set.task_id)
        
        # Calculate performance metrics
        total_validations = len(validations)
        if total_validations == 0:
            return GoldenSetPerformance(
                golden_set_id=golden_set_id,
                task_id=golden_set.task_id,
                total_validations=0,
                average_quality_score=None,
                success_rate=None,
                average_time_ms=None,
                quality_distribution={}
            )
        
        # Calculate metrics from validations
        quality_scores = [v.quality_score for v in validations if v.quality_score is not None]
        success_count = sum(1 for v in validations if v.quality_score and v.quality_score >= 0.8)
        times = [v.time_spent_ms for v in validations if v.time_spent_ms is not None]
        
        # Calculate distribution of quality scores
        quality_distribution = {}
        for score in quality_scores:
            bucket = round(score * 10) / 10  # Round to nearest 0.1
            quality_distribution[str(bucket)] = quality_distribution.get(str(bucket), 0) + 1
        
        # Convert counts to percentages
        if quality_scores:
            quality_distribution = {k: v / len(quality_scores) for k, v in quality_distribution.items()}
        
        return GoldenSetPerformance(
            golden_set_id=golden_set_id,
            task_id=golden_set.task_id,
            total_validations=total_validations,
            average_quality_score=sum(quality_scores) / len(quality_scores) if quality_scores else None,
            success_rate=success_count / total_validations if total_validations > 0 else None,
            average_time_ms=sum(times) / len(times) if times else None,
            quality_distribution=quality_distribution
        )
    
    async def get_golden_set_improvement_suggestions(self, golden_set_id: str) -> List[GoldenSetSuggestion]:
        """
        Generate suggestions for improving a golden set based on validation results.
        
        Args:
            golden_set_id: ID of the golden set
            
        Returns:
            List of improvement suggestions
            
        Raises:
            ResourceNotFound: If golden set is not found
        """
        # Get the golden set
        golden_set = self.golden_set_repository.get_by_id(golden_set_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", golden_set_id)
        
        # Get performance metrics
        performance = await self.get_golden_set_performance(golden_set_id)
        
        # Generate suggestions based on performance
        suggestions = []
        
        # If not enough validations, suggest gathering more data
        if performance.total_validations < 10:
            suggestions.append(GoldenSetSuggestion(
                suggestion_type="data_collection",
                message="Gather more validation data for more reliable metrics",
                priority="medium"
            ))
        
        # If success rate is low, suggest improvements
        if performance.success_rate is not None and performance.success_rate < 0.7:
            suggestions.append(GoldenSetSuggestion(
                suggestion_type="expected_response",
                message="Consider reviewing the expected response for accuracy or alternative formats",
                priority="high"
            ))
            
            # Suggest adding hints if none exist
            if not golden_set.hints or len(golden_set.hints) == 0:
                suggestions.append(GoldenSetSuggestion(
                    suggestion_type="hints",
                    message="Add hints to help users provide correct answers",
                    priority="medium"
                ))
        
        # If average time is high, suggest simplification
        if performance.average_time_ms and performance.average_time_ms > 10000:  # > 10 seconds
            suggestions.append(GoldenSetSuggestion(
                suggestion_type="complexity",
                message="Consider simplifying the task or providing clearer instructions",
                priority="medium"
            ))
        
        # Analyze quality distribution for bimodal patterns
        # A bimodal distribution might indicate the task is ambiguous
        if performance.quality_distribution:
            # Simple heuristic: check if there are peaks at high and low scores
            high_scores = sum(performance.quality_distribution.get(str(s), 0) for s in [0.8, 0.9, 1.0])
            low_scores = sum(performance.quality_distribution.get(str(s), 0) for s in [0.0, 0.1, 0.2])
            
            if high_scores > 0.3 and low_scores > 0.3:
                suggestions.append(GoldenSetSuggestion(
                    suggestion_type="ambiguity",
                    message="Task may be ambiguous - consider clarifying instructions or accepting alternative answers",
                    priority="high"
                ))
        
        return suggestions
    
    async def find_golden_set_candidates(self, min_agreement: float = 0.9, min_validations: int = 3) -> List[Dict[str, Any]]:
        """
        Find tasks that could be good candidates for new golden sets.
        
        This looks for tasks with high agreement among validators that aren't
        already golden sets.
        
        Args:
            min_agreement: Minimum agreement level required (0.0-1.0)
            min_validations: Minimum number of validations required
            
        Returns:
            List of candidate tasks with metadata
        """
        # Get tasks with multiple validations
        # In a real implementation, this would query the database directly
        # Here we use the validation repository as a simplification
        all_validations = self.validation_repository.get_all()
        
        # Group validations by task_id
        validations_by_task = {}
        for validation in all_validations:
            if validation.task_id not in validations_by_task:
                validations_by_task[validation.task_id] = []
            validations_by_task[validation.task_id].append(validation)
        
        # Filter for tasks with sufficient validations
        candidates = []
        for task_id, validations in validations_by_task.items():
            # Skip tasks that are already golden sets
            if self.golden_set_repository.get_by_task_id(task_id):
                continue
                
            # Need minimum number of validations
            if len(validations) < min_validations:
                continue
            
            # Get responses and their frequencies
            responses = {}
            for val in validations:
                response_key = json.dumps(val.response, sort_keys=True)
                responses[response_key] = responses.get(response_key, 0) + 1
            
            # Find the most common response and its frequency
            most_common_response = max(responses.items(), key=lambda x: x[1])
            agreement_level = most_common_response[1] / len(validations)
            
            # Check if agreement is high enough
            if agreement_level >= min_agreement:
                candidates.append({
                    "task_id": task_id,
                    "validations": len(validations),
                    "agreement_level": agreement_level,
                    "most_common_response": json.loads(most_common_response[0]),
                    "task_type": validations[0].task_type if validations else None
                })
        
        # Sort candidates by agreement level (highest first)
        candidates.sort(key=lambda x: x["agreement_level"], reverse=True)
        
        return candidates
    
    async def create_golden_set_from_candidate(
        self, task_id: str, category: str, difficulty_level: int = 1, hints: List[str] = None
    ) -> GoldenSetResponse:
        """
        Create a new golden set from a candidate task.
        
        This uses the most common response as the expected response.
        
        Args:
            task_id: ID of the candidate task
            category: Category for the golden set
            difficulty_level: Difficulty level (1-5)
            hints: Optional hints for users
            
        Returns:
            The created golden set
            
        Raises:
            ValidationError: If there aren't enough validations for the task
        """
        # Get validations for this task
        validations = self.validation_repository.find_by_task_id(task_id)
        
        if len(validations) < 3:
            raise ValidationError(
                f"Not enough validations for task {task_id}. Need at least 3, got {len(validations)}"
            )
        
        # Get the most common response
        responses = {}
        for val in validations:
            response_key = json.dumps(val.response, sort_keys=True)
            responses[response_key] = responses.get(response_key, 0) + 1
        
        most_common_response = max(responses.items(), key=lambda x: x[1])
        expected_response = json.loads(most_common_response[0])
        task_type = validations[0].task_type if validations else "unknown"
        
        # Create golden set data
        golden_set_data = GoldenSetCreate(
            task_id=task_id,
            expected_response=expected_response,
            allowed_variation=0.1,  # Default value
            hints=hints or [],
            difficulty_level=difficulty_level,
            category=category,
            task_type=task_type
        )
        
        # Create the golden set
        return await self.create_golden_set(golden_set_data)
