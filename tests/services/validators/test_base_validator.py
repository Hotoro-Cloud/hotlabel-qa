import pytest
from app.services.validators.base_validator import BaseValidator
from app.models.validation import Validation, ValidationStatus
from app.core.exceptions import ServiceException

class TestValidator(BaseValidator):
    """A test implementation of the base validator."""
    
    def __init__(self):
        self.name = "TestValidator"
        self.config = {}
    
    async def validate(self, task_id: str, validation_data: dict) -> Validation:
        if not task_id:
            raise ServiceException(
                message="Task ID cannot be empty",
                status_code=400,
                details={"error": "invalid_task_id"}
            )
        
        if validation_data is None:
            raise ServiceException(
                message="Validation data cannot be None",
                status_code=400,
                details={"error": "invalid_data"}
            )
        
        return Validation(
            task_id=task_id,
            validator_id="test_validator",
            status=ValidationStatus.PENDING,
            confidence_score=0.85,
            validation_metadata=validation_data
        )
    
    def get_metadata(self):
        return {
            "name": self.name,
            "version": "1.0.0"
        }
    
    def configure(self, config):
        if config is None:
            raise ServiceException(
                message="Configuration cannot be None",
                status_code=400,
                details={"error": "invalid_config"}
            )
        
        self.config = config
    
    async def validate_task(self, task_id: str, validation_data: dict) -> Validation:
        return await self.validate(task_id, validation_data)

@pytest.fixture
def validator():
    return TestValidator()

async def test_validator_initialization(validator):
    assert isinstance(validator, BaseValidator)
    assert validator.name == "TestValidator"

async def test_validate_task(validator):
    task_id = "test_task_1"
    validation_data = {"key": "value"}
    
    validation = await validator.validate_task(task_id, validation_data)
    
    assert isinstance(validation, Validation)
    assert validation.task_id == task_id
    assert validation.validator_id == "test_validator"
    assert validation.status == ValidationStatus.PENDING
    assert validation.confidence_score == 0.85
    assert validation.validation_metadata == validation_data

async def test_validate_task_with_invalid_data(validator):
    task_id = "test_task_2"
    validation_data = None  # Invalid data
    
    with pytest.raises(ServiceException) as exc_info:
        await validator.validate_task(task_id, validation_data)
    assert exc_info.value.status_code == 400

async def test_validate_task_with_empty_task_id(validator):
    task_id = ""
    validation_data = {"key": "value"}
    
    with pytest.raises(ServiceException) as exc_info:
        await validator.validate_task(task_id, validation_data)
    assert exc_info.value.status_code == 400

async def test_validator_metadata(validator):
    metadata = validator.get_metadata()
    
    assert "name" in metadata
    assert "version" in metadata
    assert metadata["name"] == "TestValidator"
    assert isinstance(metadata["version"], str)

async def test_validator_configuration(validator):
    config = {"threshold": 0.8}
    validator.configure(config)
    
    assert validator.config == config

async def test_validator_with_invalid_configuration(validator):
    config = None  # Invalid configuration
    
    with pytest.raises(ServiceException) as exc_info:
        validator.configure(config)
    assert exc_info.value.status_code == 400

async def test_validator_cleanup(validator):
    # Test that cleanup doesn't raise any errors
    await validator.cleanup()
    assert True  # If we get here, no exception was raised
