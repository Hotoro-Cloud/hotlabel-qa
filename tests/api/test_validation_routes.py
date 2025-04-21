import pytest
from fastapi import status
from app.models.validation import Validation, ValidationStatus

def test_create_validation(client, db_session):
    # Test data
    validation_data = {
        "task_id": "test_task_1",
        "validator_id": "test_validator_1",
        "confidence_score": 0.85,
        "metadata": {"key": "value"}
    }
    
    # Make request
    response = client.post("/api/v1/validation", json=validation_data)
    
    # Assert response
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["task_id"] == validation_data["task_id"]
    assert data["validator_id"] == validation_data["validator_id"]
    assert data["status"] == ValidationStatus.PENDING.value
    assert data["confidence_score"] == validation_data["confidence_score"]
    assert data["metadata"] == validation_data["metadata"]

def test_get_validation(client, db_session):
    # Create test validation
    validation = Validation(
        task_id="test_task_2",
        validator_id="test_validator_2",
        status=ValidationStatus.PENDING
    )
    db_session.add(validation)
    db_session.commit()
    
    # Make request
    response = client.get(f"/api/v1/validation/{validation.task_id}")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["task_id"] == validation.task_id
    assert data["validator_id"] == validation.validator_id
    assert data["status"] == validation.status.value

def test_update_validation_status(client, db_session):
    # Create test validation
    validation = Validation(
        task_id="test_task_3",
        validator_id="test_validator_3",
        status=ValidationStatus.PENDING
    )
    db_session.add(validation)
    db_session.commit()
    
    # Update data
    update_data = {
        "status": ValidationStatus.APPROVED.value
    }
    
    # Make request
    response = client.patch(
        f"/api/v1/validation/{validation.task_id}/status",
        json=update_data
    )
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == ValidationStatus.APPROVED.value

def test_list_validations(client, db_session):
    # Create test validations
    validations = [
        Validation(
            task_id=f"test_task_{i}",
            validator_id=f"test_validator_{i}",
            status=ValidationStatus.PENDING
        )
        for i in range(3)
    ]
    for validation in validations:
        db_session.add(validation)
    db_session.commit()
    
    # Make request
    response = client.get("/api/v1/validation")
    
    # Assert response
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) >= 3  # At least our test validations
    assert all(isinstance(item, dict) for item in data)

def test_validation_not_found(client):
    # Make request for non-existent validation
    response = client.get("/api/v1/validation/non_existent_task")
    
    # Assert response
    assert response.status_code == status.HTTP_404_NOT_FOUND 