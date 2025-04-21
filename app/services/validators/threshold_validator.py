from typing import Dict, Any, List, Tuple, Optional
import logging
import uuid
from datetime import datetime

from app.core.exceptions import ServiceException
from app.models.validation import Validation, ValidationStatus
from app.services.validators.base_validator import BaseValidator

logger = logging.getLogger(__name__)

class ThresholdValidator(BaseValidator):
    """Validator that applies confidence thresholds to determine validation status"""
    
    def __init__(self):
        super().__init__()
        self.name = "ThresholdValidator"
        self.config = None
        self.high_threshold = None
        self.medium_threshold = None
        self.low_threshold = None
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the validator with threshold values"""
        required_thresholds = ["high_threshold", "medium_threshold", "low_threshold"]
        
        # Check if all required thresholds are present
        if not all(key in config for key in required_thresholds):
            raise ServiceException(
                status_code=400,
                message="Missing required threshold configuration"
            )
        
        # Validate threshold values
        high = config["high_threshold"]
        medium = config["medium_threshold"]
        low = config["low_threshold"]
        
        if not all(0 <= x <= 1 for x in [high, medium, low]):
            raise ServiceException(
                status_code=400,
                message="Threshold values must be between 0 and 1"
            )
        
        if not (high > medium > low):
            raise ServiceException(
                status_code=400,
                message="Thresholds must be in order: high > medium > low"
            )
        
        self.config = config
        self.high_threshold = high
        self.medium_threshold = medium
        self.low_threshold = low
    
    async def validate(self, task_id: str, validation_data: Dict[str, Any]) -> Validation:
        """Validate a task based on confidence thresholds"""
        if not self.config:
            raise ServiceException(
                status_code=400,
                message="Validator not configured"
            )
        
        if "confidence_score" not in validation_data:
            raise ServiceException(
                status_code=400,
                message="Missing confidence_score in validation data"
            )
        
        try:
            confidence_score = float(validation_data["confidence_score"])
        except (TypeError, ValueError):
            raise ServiceException(
                status_code=400,
                message="Invalid confidence_score value"
            )
        
        if not 0 <= confidence_score <= 1:
            raise ServiceException(
                status_code=400,
                message="Confidence score must be between 0 and 1"
            )
        
        # Determine validation status based on thresholds
        if confidence_score >= self.high_threshold:
            status = ValidationStatus.APPROVED
            threshold_level = "high"
        elif confidence_score >= self.medium_threshold:
            status = ValidationStatus.PENDING
            threshold_level = "medium"
        else:
            status = ValidationStatus.REJECTED
            threshold_level = "low"
        
        # Create validation record
        validation = Validation(
            id=str(uuid.uuid4()),
            task_id=task_id,
            status=status,
            confidence_score=confidence_score,
            validation_metadata={"threshold_level": threshold_level},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return validation
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get validator metadata"""
        return {
            "name": self.name,
            "version": "1.0.0",
            "thresholds": {
                "high": self.high_threshold,
                "medium": self.medium_threshold,
                "low": self.low_threshold
            } if self.config else {}
        }
    
    async def cleanup(self) -> None:
        """Cleanup any resources"""
        pass
