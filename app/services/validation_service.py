from typing import Dict, Any, List, Optional, Tuple
import logging

from app.db.repositories.validation_repository import ValidationRepository
from app.db.repositories.golden_set_repository import GoldenSetRepository
from app.db.repositories.consensus_repository import ConsensusRepository
from app.models.validation import ValidationMethod, ValidationStatus
from app.schemas.validation import ValidationCreate, ValidationRequest, ValidationResponse
from app.services.validators import (
    GoldenSetValidator, 
    BotDetector, 
    StatisticalValidator, 
    ThresholdValidator
)
from app.core.exceptions import ValidationError, ResourceNotFound

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for validating task responses and managing the validation process"""
    
    def __init__(
        self, 
        validation_repository: ValidationRepository,
        golden_set_repository: GoldenSetRepository,
        consensus_repository: ConsensusRepository
    ):
        self.validation_repository = validation_repository
        self.golden_set_repository = golden_set_repository
        self.consensus_repository = consensus_repository
        
        # Initialize validators
        self.golden_set_validator = GoldenSetValidator(golden_set_repository)
        self.bot_detector = BotDetector(validation_repository)
        self.statistical_validator = StatisticalValidator(validation_repository)
        self.threshold_validator = ThresholdValidator()
    
    async def validate_submission(self, request: ValidationRequest) -> ValidationResponse:
        """Validate a submission and return the validation results"""
        logger.info(f"Validating submission for task {request.task_id}")
        
        # Generate a unique result ID
        import uuid
        result_id = f"result_{uuid.uuid4().hex[:8]}"
        
        # Determine validation method
        validation_method = self._determine_validation_method(request)
        
        # Create initial validation record
        validation_data = ValidationCreate(
            task_id=request.task_id,
            result_id=result_id,
            session_id=request.session_id,
            publisher_id=request.publisher_id,
            validation_method=validation_method,
            task_type=request.task_type,
            response=request.response,
            time_spent_ms=request.time_spent_ms
        )
        
        validation = self.validation_repository.create(validation_data)
        
        # Perform validation based on the method
        quality_score, confidence, issues, feedback = await self._perform_validation(
            validation_method=validation_method,
            task_id=request.task_id,
            response=request.response,
            session_id=request.session_id,
            publisher_id=request.publisher_id,
            task_type=request.task_type,
            time_spent_ms=request.time_spent_ms
        )
        
        # Update validation with results
        validation = self.validation_repository.update(
            validation_id=validation.id,
            update_data={
                "quality_score": quality_score,
                "confidence": confidence,
                "issues_detected": issues,
                "feedback": feedback,
                "status": self._determine_status(quality_score, confidence)
            }
        )
        
        # Handle consensus validation if needed
        if validation.status == ValidationStatus.NEEDS_REVIEW:
            await self._handle_consensus_validation(validation)
        
        # Convert to response model
        return self._to_response_model(validation)
    
    def _determine_validation_method(self, request: ValidationRequest) -> ValidationMethod:
        """Determine the best validation method for this submission"""
        # If a specific validation method is requested, use it
        if request.validation_type:
            return request.validation_type
        
        # Check if this is a golden set task
        golden_set = self.golden_set_repository.get_by_task_id(request.task_id)
        if golden_set:
            return ValidationMethod.GOLDEN_SET
        
        # Default to using all validation methods
        return ValidationMethod.THRESHOLD
    
    async def _perform_validation(
        self, validation_method: ValidationMethod, task_id: str, response: Any, session_id: str, **kwargs
    ) -> Tuple[float, float, List[Dict[str, Any]], Optional[str]]:
        """Perform validation using the specified method"""
        quality_score = 0.0
        confidence = 0.0
        issues = []
        feedback = None
        
        if validation_method == ValidationMethod.GOLDEN_SET:
            # Validate against golden set
            quality_score, confidence, issues, feedback = await self.golden_set_validator.validate(
                task_id, response, session_id, **kwargs
            )
            
        elif validation_method == ValidationMethod.BOT_DETECTION:
            # Validate for bot-like behavior
            quality_score, confidence, issues, feedback = await self.bot_detector.validate(
                task_id, response, session_id, **kwargs
            )
            
        elif validation_method == ValidationMethod.STATISTICAL:
            # Validate using statistical methods
            quality_score, confidence, issues, feedback = await self.statistical_validator.validate(
                task_id, response, session_id, **kwargs
            )
            
        elif validation_method == ValidationMethod.THRESHOLD:
            # Validate using threshold methods
            quality_score, confidence, issues, feedback = await self.threshold_validator.validate(
                task_id, response, session_id, **kwargs
            )
            
        else:
            # Combine all validation methods for comprehensive assessment
            # Run multiple validators and combine their results with appropriate weights
            threshold_result = await self.threshold_validator.validate(task_id, response, session_id, **kwargs)
            bot_result = await self.bot_detector.validate(task_id, response, session_id, **kwargs)
            statistical_result = await self.statistical_validator.validate(task_id, response, session_id, **kwargs)
            
            # Golden set validation only if a golden set exists
            golden_set = self.golden_set_repository.get_by_task_id(task_id)
            if golden_set:
                golden_result = await self.golden_set_validator.validate(task_id, response, session_id, **kwargs)
                # Golden set has highest priority if available
                quality_score = golden_result[0] * 0.5 + threshold_result[0] * 0.2 + bot_result[0] * 0.2 + statistical_result[0] * 0.1
                confidence = golden_result[1] * 0.5 + threshold_result[1] * 0.2 + bot_result[1] * 0.2 + statistical_result[1] * 0.1
                issues = golden_result[2] + threshold_result[2] + bot_result[2] + statistical_result[2]
                feedback = golden_result[3] or bot_result[3] or threshold_result[3] or statistical_result[3]
            else:
                # Without golden set, balance other validators
                quality_score = threshold_result[0] * 0.4 + bot_result[0] * 0.3 + statistical_result[0] * 0.3
                confidence = threshold_result[1] * 0.4 + bot_result[1] * 0.3 + statistical_result[1] * 0.3
                issues = threshold_result[2] + bot_result[2] + statistical_result[2]
                feedback = bot_result[3] or threshold_result[3] or statistical_result[3]
        
        return quality_score, confidence, issues, feedback
    
    def _determine_status(self, quality_score: float, confidence: float) -> ValidationStatus:
        """Determine validation status based on quality score and confidence"""
        from app.core.config import settings
        
        if confidence >= settings.HIGH_CONFIDENCE_THRESHOLD:
            # High confidence - can make definitive judgment
            if quality_score >= 0.7:  # Good quality
                return ValidationStatus.VALIDATED
            else:  # Poor quality
                return ValidationStatus.REJECTED
        elif confidence >= settings.MEDIUM_CONFIDENCE_THRESHOLD:
            # Medium confidence - might need review
            return ValidationStatus.NEEDS_REVIEW
        else:
            # Low confidence - definitely needs review
            return ValidationStatus.NEEDS_REVIEW
    
    async def _handle_consensus_validation(self, validation) -> None:
        """Handle consensus validation for medium-confidence results"""
        # Check if a consensus group already exists for this task
        consensus_group = self.consensus_repository.get_by_task_id(validation.task_id)
        
        if not consensus_group:
            # Create a new consensus group
            from app.schemas.consensus import ConsensusGroupCreate
            from app.core.config import settings
            
            consensus_data = ConsensusGroupCreate(
                task_id=validation.task_id,
                required_validations=settings.MINIMUM_CONSENSUS_VALIDATORS,
                agreement_threshold=settings.CONSENSUS_REQUIRED_AGREEMENT
            )
            consensus_group = self.consensus_repository.create(consensus_data)
        
        # Add this validation to the consensus group
        self.consensus_repository.add_validation(consensus_group.id, validation)
        
        # Check if we have enough validations to determine consensus
        self.consensus_repository.check_and_update_consensus(consensus_group.id)
    
    def _to_response_model(self, validation) -> ValidationResponse:
        """Convert database model to response schema"""
        # In a real implementation, this would be more comprehensive
        return ValidationResponse(
            id=validation.id,
            task_id=validation.task_id,
            result_id=validation.result_id,
            session_id=validation.session_id,
            publisher_id=validation.publisher_id,
            validation_method=validation.validation_method,
            status=validation.status,
            quality_score=validation.quality_score,
            confidence=validation.confidence,
            task_type=validation.task_type,
            response=validation.response,
            time_spent_ms=validation.time_spent_ms,
            issues_detected=validation.issues_detected,
            feedback=validation.feedback,
            created_at=validation.created_at,
            updated_at=validation.updated_at
        )
    
    async def get_validation(self, validation_id: str) -> ValidationResponse:
        """Get a validation by ID"""
        validation = self.validation_repository.get_by_id(validation_id)
        if not validation:
            raise ResourceNotFound("Validation", validation_id)
        
        return self._to_response_model(validation)
    
    async def get_validation_by_result(self, result_id: str) -> ValidationResponse:
        """Get a validation by result ID"""
        validation = self.validation_repository.get_by_result_id(result_id)
        if not validation:
            raise ResourceNotFound("Validation", f"with result_id {result_id}")
        
        return self._to_response_model(validation)
