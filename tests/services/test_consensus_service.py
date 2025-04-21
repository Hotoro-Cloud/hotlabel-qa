import pytest
from datetime import datetime
from app.services.consensus import ConsensusService
from app.models.consensus import Consensus, ConsensusStatus
from app.models.validation import Validation, ValidationStatus
from app.core.exceptions import ServiceException

@pytest.fixture
def consensus_service(db_session):
    return ConsensusService(db_session)

@pytest.fixture
def sample_validations(db_session):
    # Create sample validations for consensus
    validations = [
        Validation(
            task_id="test_task_1",
            validator_id=f"validator_{i}",
            status=ValidationStatus.APPROVED,
            confidence_score=0.85 + (i * 0.05),
            created_at=datetime.utcnow()
        )
        for i in range(3)
    ]
    for validation in validations:
        db_session.add(validation)
    db_session.commit()
    return validations

@pytest.fixture
def sample_consensus(db_session, sample_validations):
    consensus = Consensus(
        task_id="test_task_1",
        status=ConsensusStatus.PENDING,
        agreement_score=0.8,
        validator_count=len(sample_validations),
        created_at=datetime.utcnow()
    )
    db_session.add(consensus)
    db_session.commit()
    return consensus

async def test_create_consensus(consensus_service, sample_validations):
    consensus = await consensus_service.create_consensus("test_task_1")
    
    assert consensus.task_id == "test_task_1"
    assert consensus.status == ConsensusStatus.PENDING
    assert consensus.validator_count == len(sample_validations)
    assert 0 <= consensus.agreement_score <= 1

async def test_get_consensus(consensus_service, sample_consensus):
    consensus = await consensus_service.get_consensus(sample_consensus.task_id)
    
    assert consensus.task_id == sample_consensus.task_id
    assert consensus.status == sample_consensus.status
    assert consensus.agreement_score == sample_consensus.agreement_score
    assert consensus.validator_count == sample_consensus.validator_count

async def test_get_consensus_not_found(consensus_service):
    with pytest.raises(ServiceException) as exc_info:
        await consensus_service.get_consensus("non_existent_task")
    assert exc_info.value.status_code == 404

async def test_update_consensus_status(consensus_service, sample_consensus):
    new_status = ConsensusStatus.REACHED
    updated_consensus = await consensus_service.update_consensus_status(
        sample_consensus.task_id,
        new_status
    )
    
    assert updated_consensus.status == new_status
    assert updated_consensus.task_id == sample_consensus.task_id

async def test_calculate_agreement_score(consensus_service, db_session):
    # Create validations with different statuses
    validations = [
        Validation(
            task_id="agreement_task",
            validator_id=f"validator_{i}",
            status=status,
            confidence_score=0.9
        )
        for i, status in enumerate([
            ValidationStatus.APPROVED,
            ValidationStatus.APPROVED,
            ValidationStatus.REJECTED,
            ValidationStatus.APPROVED
        ])
    ]
    for validation in validations:
        db_session.add(validation)
    db_session.commit()
    
    agreement_score = await consensus_service.calculate_agreement_score("agreement_task")
    assert agreement_score == 0.75  # 3 out of 4 validators agree

async def test_list_consensus(consensus_service, db_session):
    # Create multiple consensus records
    consensus_records = [
        Consensus(
            task_id=f"task_{i}",
            status=ConsensusStatus.PENDING,
            agreement_score=0.8 + (i * 0.05),
            validator_count=3
        )
        for i in range(3)
    ]
    for consensus in consensus_records:
        db_session.add(consensus)
    db_session.commit()
    
    # Test listing all consensus
    result = await consensus_service.list_consensus()
    assert len(result) >= 3
    
    # Test filtering by status
    pending_consensus = await consensus_service.list_consensus(
        status=ConsensusStatus.PENDING
    )
    assert all(c.status == ConsensusStatus.PENDING for c in pending_consensus)
    
    # Test filtering by agreement threshold
    high_agreement = await consensus_service.list_consensus(
        min_agreement=0.85
    )
    assert all(c.agreement_score >= 0.85 for c in high_agreement)

async def test_delete_consensus(consensus_service, sample_consensus):
    await consensus_service.delete_consensus(sample_consensus.task_id)
    
    # Verify deletion
    with pytest.raises(ServiceException) as exc_info:
        await consensus_service.get_consensus(sample_consensus.task_id)
    assert exc_info.value.status_code == 404

async def test_consensus_statistics(consensus_service, db_session):
    # Create consensus records with different statuses
    consensus_records = [
        Consensus(
            task_id=f"task_{i}",
            status=status,
            agreement_score=0.8,
            validator_count=3
        )
        for i, status in enumerate([
            ConsensusStatus.REACHED,
            ConsensusStatus.PENDING,
            ConsensusStatus.FAILED
        ])
    ]
    for consensus in consensus_records:
        db_session.add(consensus)
    db_session.commit()
    
    stats = await consensus_service.get_consensus_statistics()
    
    assert "total_consensus" in stats
    assert "status_distribution" in stats
    assert "average_agreement" in stats
    
    assert stats["total_consensus"] == len(consensus_records)
    assert stats["status_distribution"]["reached"] == 1
    assert stats["status_distribution"]["pending"] == 1
    assert stats["status_distribution"]["failed"] == 1
    assert abs(stats["average_agreement"] - 0.8) < 0.01 