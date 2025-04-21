"""
Golden Set Service for managing golden set examples.

This service provides functionality for creating, updating, and managing
golden set examples that are used for validation and quality control.
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import json
from datetime import datetime
import uuid

from app.db.repositories.golden_set_repository import GoldenSetRepository
from app.db.repositories.validation_repository import ValidationRepository
from app.schemas.golden_set import GoldenSetCreate, GoldenSetResponse
from app.core.exceptions import ResourceNotFound, ValidationError

logger = logging.getLogger(__name__)

class GoldenSetService:
    """
    Service for managing golden set examples.
    
    Golden sets are curated examples with known correct answers that serve as
    a high-confidence validation method and training tool for quality assurance.
    """
    
    def __init__(
        self, 
        golden_set_repository: GoldenSetRepository,
        validation_repository: ValidationRepository
    ):
        """
        Initialize the golden set service.
        
        Args:
            golden_set_repository: Repository for golden set data access
            validation_repository: Repository for validation data access
        """
        self.golden_set_repository = golden_set_repository
        self.validation_repository = validation_repository
    
    async def create_golden_set(
        self, golden_set_data: dict
    ) -> GoldenSetResponse:
        """
        Create a new golden set example.
        
        Args:
            golden_set_data: Data for the golden set to create
            
        Returns:
            GoldenSetResponse: Created golden set
            
        Raises:
            ValidationError: If the golden set data is invalid
        """
        # Validate input
        if isinstance(golden_set_data, dict):
            # Convert dict to GoldenSetCreate
            from app.schemas.golden_set import GoldenSetCreate
            
            # Validate required fields
            if "task_id" not in golden_set_data:
                raise ValidationError("task_id is required", "task_id")
                
            # Create GoldenSetCreate object
            golden_set_create = GoldenSetCreate(
                task_id=golden_set_data["task_id"],
                expected_response=golden_set_data.get("expected_response", {}),
                allowed_variation=golden_set_data.get("allowed_variation", 0.1),
                difficulty_level=golden_set_data.get("difficulty_level", 1),
                category=golden_set_data.get("category", "unknown"),
                tags=golden_set_data.get("tags", [])
            )
            
            # Add confidence_score if not provided
            if not hasattr(golden_set_data, "confidence_score") and isinstance(golden_set_data, dict) and "confidence_score" not in golden_set_data:
                golden_set_data["confidence_score"] = 1.0
            golden_set_data = golden_set_create
            
            # Ensure expected_response is set
            if not golden_set_data.expected_response:
                golden_set_data.expected_response = {}
            
        self._validate_golden_set(golden_set_data)
        
        # Check if golden set already exists for this task
        existing_golden_set = self.golden_set_repository.get_by_task_id(golden_set_data.task_id)
        if existing_golden_set:
            raise ValidationError(
                f"Golden set already exists for task {golden_set_data.task_id}",
                "task_id"
            )
        
        # Create golden set
        try:
            golden_set = self.golden_set_repository.create(golden_set_data)
            logger.info(f"Created golden set {golden_set.id} for task {golden_set.task_id}")
            
            # Convert to response model
            return GoldenSetResponse.from_orm(golden_set)
        except Exception as e:
            logger.error(f"Error creating golden set: {str(e)}")
            raise ValidationError(f"Error creating golden set: {str(e)}")
    
    async def update_golden_set(
        self, golden_set_id: str, update_data: Dict[str, Any]
    ) -> GoldenSetResponse:
        """
        Update an existing golden set.
        
        Args:
            golden_set_id: ID of the golden set to update
            update_data: Data to update
            
        Returns:
            GoldenSetResponse: Updated golden set
            
        Raises:
            ResourceNotFound: If the golden set is not found
            ValidationError: If the update data is invalid
        """
        # Get existing golden set
        golden_set = self.golden_set_repository.get_by_id(golden_set_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", golden_set_id)
        
        # Validate update data
        if "expected_response" in update_data:
            self._validate_expected_response(update_data["expected_response"])
        
        if "allowed_variation" in update_data:
            if not 0.0 <= update_data["allowed_variation"] <= 1.0:
                raise ValidationError(
                    "allowed_variation must be between 0.0 and 1.0",
                    "allowed_variation"
                )
        
        # Update golden set
        try:
            updated_golden_set = self.golden_set_repository.update(
                golden_set_id, update_data
            )
            if not updated_golden_set:
                raise ResourceNotFound("GoldenSet", golden_set_id)
                
            logger.info(f"Updated golden set {golden_set_id}")
            
            # Convert to response model
            return GoldenSetResponse.from_orm(updated_golden_set)
        except ResourceNotFound:
            raise
        except Exception as e:
            logger.error(f"Error updating golden set {golden_set_id}: {str(e)}")
            raise ValidationError(f"Error updating golden set: {str(e)}")
    
    async def get_golden_set(self, golden_set_id: str) -> GoldenSetResponse:
        """
        Get a golden set by ID or task ID.
        
        Args:
            golden_set_id: ID of the golden set or task ID to retrieve
            
        Returns:
            GoldenSetResponse: Golden set data
            
        Raises:
            ResourceNotFound: If the golden set is not found
        """
        # Try to get by ID first
        golden_set = self.golden_set_repository.get_by_id(golden_set_id)
        
        # If not found, try to get by task_id
        if not golden_set:
            golden_set = self.golden_set_repository.get_by_task_id(golden_set_id)
            
        if not golden_set:
            raise ResourceNotFound("GoldenSet", golden_set_id)
            
        return GoldenSetResponse.from_orm(golden_set)
    
    async def get_golden_set_by_task(self, task_id: str) -> GoldenSetResponse:
        """
        Get a golden set by task ID.
        
        Args:
            task_id: ID of the task
            
        Returns:
            GoldenSetResponse: Golden set data
            
        Raises:
            ResourceNotFound: If no golden set exists for the task
        """
        golden_set = self.golden_set_repository.get_by_task_id(task_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", f"for task {task_id}")
            
        return GoldenSetResponse.from_orm(golden_set)
    
    async def list_golden_sets(
        self, 
        category: Optional[str] = None, 
        status = None,
        min_confidence = None,
        limit: int = 100, 
        offset: int = 0
    ) -> List[GoldenSetResponse]:
        """
        List golden sets, optionally filtered by category.
        
        Args:
            category: Category to filter by
            status: Status to filter by
            min_confidence: Minimum confidence score
            limit: Maximum number of results
            offset: Pagination offset
            
        Returns:
            List[GoldenSetResponse]: List of golden sets
        """
        filters = {}
        if category:
            filters["category"] = category
        if status:
            filters["status"] = status
        if min_confidence is not None:
            filters["min_confidence"] = min_confidence
            
        golden_sets = self.golden_set_repository.list(filters, limit, offset)
        return [GoldenSetResponse.from_orm(gs) for gs in golden_sets]
        
    async def update_golden_set_status(self, task_id: str, status) -> GoldenSetResponse:
        """
        Update the status of a golden set.
        
        Args:
            task_id: ID of the task
            status: New status
            
        Returns:
            GoldenSetResponse: Updated golden set
            
        Raises:
            ResourceNotFound: If no golden set exists for the task
        """
        golden_set = self.golden_set_repository.get_by_task_id(task_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", f"with ID {task_id} not found")
            
        update_data = {"status": status}
        updated_golden_set = self.golden_set_repository.update(golden_set.id, update_data)
        return GoldenSetResponse.from_orm(updated_golden_set)
        
    async def delete_golden_set(self, task_id: str) -> None:
        """
        Delete a golden set.
        
        Args:
            task_id: ID of the task
            
        Raises:
            ResourceNotFound: If no golden set exists for the task
        """
        golden_set = self.golden_set_repository.get_by_task_id(task_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", f"with ID {task_id} not found")
            
        self.golden_set_repository.delete(golden_set.id)
        
    async def get_golden_set_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about golden sets.
        
        Returns:
            Dict: Statistics about golden sets
        """
        golden_sets = self.golden_set_repository.list({})
        
        if not golden_sets:
            return {
                "total_golden_sets": 0,
                "status_distribution": {},
                "average_confidence": 0.0
            }
            
        # Calculate statistics
        total = len(golden_sets)
        
        # Status distribution
        status_distribution = {}
        for gs in golden_sets:
            status = gs.status.value if hasattr(gs.status, 'value') else gs.status
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
        # Average confidence
        confidence_scores = [gs.confidence_score for gs in golden_sets if gs.confidence_score is not None]
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        return {
            "total_golden_sets": total,
            "status_distribution": status_distribution,
            "average_confidence": avg_confidence
        }
    
    async def create_golden_set_from_validation(
        self, validation_id: str, allowed_variation: float = 0.1
    ) -> GoldenSetResponse:
        """
        Create a golden set from an existing validation result.
        
        This enables a feedback loop where high-quality validations
        can be promoted to golden set examples.
        
        Args:
            validation_id: ID of the validation to use
            allowed_variation: Allowed variation in matching (0.0-1.0)
            
        Returns:
            GoldenSetResponse: Created golden set
            
        Raises:
            ResourceNotFound: If the validation is not found
            ValidationError: If the validation can't be converted
        """
        # Get validation
        validation = self.validation_repository.get_by_id(validation_id)
        if not validation:
            raise ResourceNotFound("Validation", validation_id)
            
        # Check validation quality
        if validation.quality_score < 0.9:
            raise ValidationError(
                f"Validation quality score ({validation.quality_score}) is too low for conversion to golden set",
                "validation_id"
            )
            
        # Check if golden set already exists
        existing_golden_set = self.golden_set_repository.get_by_task_id(validation.task_id)
        if existing_golden_set:
            raise ValidationError(
                f"Golden set already exists for task {validation.task_id}",
                "task_id"
            )
            
        # Create golden set data
        golden_set_data = GoldenSetCreate(
            task_id=validation.task_id,
            expected_response=validation.response,
            allowed_variation=allowed_variation,
            difficulty_level=1,  # Default level
            category=validation.task_type or "unknown",
            tags=[]
        )
        
        # Create golden set
        try:
            golden_set = self.golden_set_repository.create(golden_set_data)
            
            # Link validation to golden set
            self.golden_set_repository.link_validation(golden_set.id, validation_id)
            
            logger.info(
                f"Created golden set {golden_set.id} from validation {validation_id}"
            )
            
            # Convert to response model
            return GoldenSetResponse.from_orm(golden_set)
        except Exception as e:
            logger.error(f"Error creating golden set from validation: {str(e)}")
            raise ValidationError(f"Error creating golden set: {str(e)}")
    
    async def evaluate_golden_set(self, golden_set_id: str) -> Dict[str, Any]:
        """
        Evaluate a golden set's performance based on validation results.
        
        Args:
            golden_set_id: ID of the golden set to evaluate
            
        Returns:
            Dict: Evaluation metrics
            
        Raises:
            ResourceNotFound: If the golden set is not found
        """
        # Get golden set
        golden_set = self.golden_set_repository.get_by_id(golden_set_id)
        if not golden_set:
            raise ResourceNotFound("GoldenSet", golden_set_id)
            
        # Get validations for the task
        validations = self.validation_repository.get_by_task_id(golden_set.task_id)
        
        # Calculate metrics
        total_validations = len(validations)
        if total_validations == 0:
            return {
                "golden_set_id": golden_set_id,
                "task_id": golden_set.task_id,
                "total_validations": 0,
                "average_quality_score": None,
                "pass_rate": None,
                "usage_count": 0
            }
            
        # Calculate metrics
        quality_scores = [v.quality_score for v in validations if v.quality_score is not None]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        # Calculate pass rate (validations that match the golden set within allowed variation)
        pass_count = sum(1 for v in validations 
                         if v.quality_score is not None and v.quality_score >= (1.0 - golden_set.allowed_variation))
        pass_rate = pass_count / total_validations if total_validations > 0 else None
        
        return {
            "golden_set_id": golden_set_id,
            "task_id": golden_set.task_id,
            "total_validations": total_validations,
            "average_quality_score": avg_quality,
            "pass_rate": pass_rate,
            "usage_count": total_validations
        }
    
    def _validate_golden_set(self, golden_set_data: GoldenSetCreate) -> None:
        """
        Validate golden set data before creation.
        
        Args:
            golden_set_data: Data to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for required fields
        if not golden_set_data.task_id:
            raise ValidationError("task_id is required", "task_id")
            
        # Set default expected_response if not provided
        if not golden_set_data.expected_response:
            golden_set_data.expected_response = {}
            
        # Set default category if not provided
        if not golden_set_data.category:
            golden_set_data.category = "unknown"
            
        # Validate expected response
        self._validate_expected_response(golden_set_data.expected_response)
        
        # Validate allowed variation
        if not 0.0 <= golden_set_data.allowed_variation <= 1.0:
            raise ValidationError(
                "allowed_variation must be between 0.0 and 1.0",
                "allowed_variation"
            )
    
    def _validate_expected_response(self, expected_response: Any) -> None:
        """
        Validate that the expected response is in a supported format.
        
        Args:
            expected_response: Response to validate
            
        Raises:
            ValidationError: If validation fails
        """
        # Check for supported types
        if not isinstance(expected_response, (str, int, float, list, dict)):
            raise ValidationError(
                "expected_response must be a string, number, list, or object",
                "expected_response"
            )
            
        # For lists, check that they are not empty
        if isinstance(expected_response, list) and not expected_response:
            raise ValidationError(
                "expected_response list cannot be empty",
                "expected_response"
            )
