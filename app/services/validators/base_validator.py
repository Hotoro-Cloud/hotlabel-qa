"""
Base validator class for quality assurance.

This abstract base class defines the interface that all validators must implement.
"""
from typing import Dict, Any, List, Tuple, Optional

class BaseValidator:
    """
    Abstract base class for validators.
    
    All validator implementations should inherit from this class and implement
    the validate method.
    """
    
    async def validate(
        self, task_id: str, response: Any, session_id: str, **kwargs
    ) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        """
        Validate a response.
        
        Args:
            task_id: ID of the task being validated
            response: The response to validate
            session_id: Session ID of the user
            **kwargs: Additional validation context
            
        Returns:
            Tuple containing:
            - quality_score (float): 0-1 score indicating response quality
            - confidence (float): 0-1 score indicating confidence in the validation
            - issues (list): List of detected issues
            - feedback (str): Optional feedback for the user
        """
        raise NotImplementedError("Subclasses must implement validate method")