"""
Base validator class for quality assurance.

This abstract base class defines the interface that all validators must implement.
"""
from typing import Dict, Any, Optional
from app.models.validation import Validation

class BaseValidator:
    """
    Abstract base class for validators.
    
    All validator implementations should inherit from this class and implement
    the validate method.
    """
    
    async def validate(self, task_id: str, validation_data: Dict[str, Any]) -> Validation:
        """
        Validate a task.
        
        Args:
            task_id: ID of the task being validated
            validation_data: Data needed for validation
            
        Returns:
            Validation object containing the validation results
        """
        raise NotImplementedError("Subclasses must implement validate method")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get validator metadata.
        
        Returns:
            Dictionary containing validator metadata
        """
        raise NotImplementedError("Subclasses must implement get_metadata method")
    
    async def cleanup(self) -> None:
        """
        Cleanup any resources used by the validator.
        """
        pass