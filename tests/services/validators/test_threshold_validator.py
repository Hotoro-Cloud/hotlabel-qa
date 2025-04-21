import pytest
from app.services.validators.threshold_validator import ThresholdValidator
from app.models.validation import Validation, ValidationStatus
from app.core.exceptions import ServiceException

@pytest.fixture
def validator():
    return ThresholdValidator()

@pytest.fixture
def configured_validator():
    validator = ThresholdValidator()
    validator.configure({
        "high_threshold": 0.85,
        "medium_threshold": 0.60,
        "low_threshold": 0.40
    })
    return validator

async def test_validator_initialization(validator):
    assert isinstance(validator, ThresholdValidator)
    assert validator.name == "ThresholdValidator"
    assert validator.config is None

async def test_validator_configuration(validator):
    config = {
        "high_threshold": 0.85,
        "medium_threshold": 0.60,
        "low_threshold": 0.40
    }
    validator.configure(config)
    
    assert validator.config == config
    assert validator.high_threshold == 0.85
    assert validator.medium_threshold == 0.60
    assert validator.low_threshold == 0.40

async def test_validator_with_invalid_configuration(validator):
    # Test missing thresholds
    config = {"high_threshold": 0.85}
    with pytest.raises(ServiceException) as exc_info:
        validator.configure(config)
    assert exc_info.value.status_code == 400
    
    # Test invalid threshold values
    config = {
        "high_threshold": 1.5,  # Invalid value
        "medium_threshold": 0.60,
        "low_threshold": 0.40
    }
    with pytest.raises(ServiceException) as exc_info:
        validator.configure(config)
    assert exc_info.value.status_code == 400
    
    # Test thresholds in wrong order
    config = {
        "high_threshold": 0.60,
        "medium_threshold": 0.85,
        "low_threshold": 0.40
    }
    with pytest.raises(ServiceException) as exc_info:
        validator.configure(config)
    assert exc_info.value.status_code == 400

async def test_validate_high_confidence(configured_validator):
    task_id = "test_task_1"
    validation_data = {"confidence_score": 0.90}
    
    validation = await configured_validator.validate(task_id, validation_data)
    
    assert validation.task_id == task_id
    assert validation.status == ValidationStatus.APPROVED
    assert validation.confidence_score == 0.90
    assert "threshold_level" in validation.validation_metadata
    assert validation.validation_metadata["threshold_level"] == "high"

async def test_validate_medium_confidence(configured_validator):
    task_id = "test_task_2"
    validation_data = {"confidence_score": 0.70}
    
    validation = await configured_validator.validate(task_id, validation_data)
    
    assert validation.task_id == task_id
    assert validation.status == ValidationStatus.PENDING
    assert validation.confidence_score == 0.70
    assert validation.validation_metadata["threshold_level"] == "medium"

async def test_validate_low_confidence(configured_validator):
    task_id = "test_task_3"
    validation_data = {"confidence_score": 0.50}
    
    validation = await configured_validator.validate(task_id, validation_data)
    
    assert validation.task_id == task_id
    assert validation.status == ValidationStatus.REJECTED
    assert validation.confidence_score == 0.50
    assert validation.validation_metadata["threshold_level"] == "low"

async def test_validate_without_confidence_score(configured_validator):
    task_id = "test_task_4"
    validation_data = {}  # Missing confidence score
    
    with pytest.raises(ServiceException) as exc_info:
        await configured_validator.validate(task_id, validation_data)
    assert exc_info.value.status_code == 400

async def test_validate_with_invalid_confidence_score(configured_validator):
    task_id = "test_task_5"
    validation_data = {"confidence_score": "invalid"}  # Invalid confidence score
    
    with pytest.raises(ServiceException) as exc_info:
        await configured_validator.validate(task_id, validation_data)
    assert exc_info.value.status_code == 400

async def test_validator_metadata(validator):
    metadata = validator.get_metadata()
    
    assert "name" in metadata
    assert "version" in metadata
    assert "thresholds" in metadata
    assert metadata["name"] == "ThresholdValidator"
    assert isinstance(metadata["version"], str)
    assert isinstance(metadata["thresholds"], dict)

async def test_validator_cleanup(validator):
    # Test that cleanup doesn't raise any errors
    await validator.cleanup()
    assert True  # If we get here, no exception was raised
