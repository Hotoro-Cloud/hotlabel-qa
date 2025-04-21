import pytest
from datetime import datetime, timedelta
from app.services.metrics_service import MetricsService
from app.models.validation import Validation, ValidationStatus

@pytest.fixture
def metrics_service(db_session):
    return MetricsService(db_session)

@pytest.fixture
def sample_validations(db_session):
    # Create sample validations with different statuses and timestamps
    validations = [
        Validation(
            task_id=f"task_{i}",
            validator_id=f"validator_{i}",
            status=status,
            confidence_score=0.8 + (i * 0.05),
            created_at=datetime.utcnow() - timedelta(days=i)
        )
        for i, status in enumerate([
            ValidationStatus.APPROVED,
            ValidationStatus.REJECTED,
            ValidationStatus.PENDING,
            ValidationStatus.REVIEW
        ])
    ]
    for validation in validations:
        db_session.add(validation)
    db_session.commit()
    return validations

async def test_calculate_validation_metrics(metrics_service, sample_validations):
    metrics = await metrics_service.calculate_validation_metrics()
    
    assert "total_validations" in metrics
    assert "status_distribution" in metrics
    assert "average_quality_score" in metrics
    
    # Verify counts
    assert metrics["total_validations"] == len(sample_validations)
    assert metrics["status_distribution"]["approved"] == 1
    assert metrics["status_distribution"]["rejected"] == 1
    assert metrics["status_distribution"]["pending"] == 1
    assert metrics["status_distribution"]["review"] == 1

async def test_calculate_validator_metrics(metrics_service, sample_validations):
    metrics = await metrics_service.calculate_validator_metrics()
    
    # Check that each validator has metrics
    for validator_id in [v.validator_id for v in sample_validations]:
        assert validator_id in metrics
        assert "total_validations" in metrics[validator_id]
        assert "average_quality_score" in metrics[validator_id]
        assert "status_distribution" in metrics[validator_id]

async def test_calculate_quality_metrics(metrics_service, sample_validations):
    metrics = await metrics_service.calculate_quality_metrics()
    
    assert "validation_metrics" in metrics
    assert "validator_metrics" in metrics
    assert "overall_quality_score" in metrics
    
    # Verify quality score
    assert 0 <= metrics["overall_quality_score"] <= 1

async def test_get_metrics_with_time_range(metrics_service, sample_validations):
    # Test metrics for last 7 days
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    
    metrics = await metrics_service.get_metrics(
        start_date=start_date,
        end_date=end_date
    )
    
    assert "period" in metrics
    assert "metrics" in metrics
    
    # Verify time range filtering
    assert metrics["metrics"]["total_labels"] == len(sample_validations)

async def test_get_metrics_with_invalid_time_range(metrics_service):
    # Test with invalid time range (end date before start date)
    end_date = datetime.utcnow() - timedelta(days=7)
    start_date = datetime.utcnow()
    
    from app.core.exceptions import ValidationError
    with pytest.raises(ValidationError):
        await metrics_service.get_metrics(
            start_date=start_date,
            end_date=end_date
        )
