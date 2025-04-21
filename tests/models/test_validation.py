import pytest
from datetime import datetime
from app.models.validation import Validation, ValidationStatus

def test_validation_model(db_session):
    # Create a validation record
    validation = Validation(
        task_id="test_task_1",
        validator_id="test_validator_1",
        status=ValidationStatus.PENDING,
        confidence_score=0.85,
        metadata={"key": "value"},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    # Add to database
    db_session.add(validation)
    db_session.commit()
    
    # Retrieve from database
    retrieved = db_session.query(Validation).filter_by(task_id="test_task_1").first()
    
    # Assert fields
    assert retrieved.task_id == "test_task_1"
    assert retrieved.validator_id == "test_validator_1"
    assert retrieved.status == ValidationStatus.PENDING
    assert retrieved.confidence_score == 0.85
    assert retrieved.metadata == {"key": "value"}
    assert isinstance(retrieved.created_at, datetime)
    assert isinstance(retrieved.updated_at, datetime)

def test_validation_status_enum():
    # Test all status values
    assert ValidationStatus.PENDING.value == "pending"
    assert ValidationStatus.APPROVED.value == "approved"
    assert ValidationStatus.REJECTED.value == "rejected"
    assert ValidationStatus.REVIEW.value == "review"

def test_validation_relationships(db_session):
    # Create a validation with relationships
    validation = Validation(
        task_id="test_task_2",
        validator_id="test_validator_2",
        status=ValidationStatus.PENDING
    )
    
    db_session.add(validation)
    db_session.commit()
    
    # Test cascade delete
    db_session.delete(validation)
    db_session.commit()
    
    # Verify deletion
    assert db_session.query(Validation).filter_by(task_id="test_task_2").first() is None 