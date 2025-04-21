from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.repositories.consensus_repository import ConsensusRepository
from app.schemas.consensus import (
    ConsensusCreate,
    ConsensusUpdate,
    ConsensusInDB,
    ConsensusFilter,
    ConsensusStatistics
)

router = APIRouter(prefix="/consensus", tags=["consensus"])

@router.post("/", response_model=ConsensusInDB)
def create_consensus(
    consensus_create: ConsensusCreate,
    db: Session = Depends(get_db)
) -> ConsensusInDB:
    """Create a new consensus record."""
    repository = ConsensusRepository(db)
    
    # Check if consensus already exists for task
    if repository.get_by_task_id(consensus_create.task_id):
        raise HTTPException(
            status_code=400,
            detail=f"Consensus already exists for task {consensus_create.task_id}"
        )
    
    return repository.create(consensus_create)

@router.get("/{task_id}", response_model=ConsensusInDB)
def get_consensus(
    task_id: str,
    db: Session = Depends(get_db)
) -> ConsensusInDB:
    """Get consensus by task ID."""
    repository = ConsensusRepository(db)
    consensus = repository.get_by_task_id(task_id)
    if not consensus:
        raise HTTPException(
            status_code=404,
            detail=f"Consensus not found for task {task_id}"
        )
    return consensus

@router.get("/", response_model=List[ConsensusInDB])
def list_consensus(
    filters: ConsensusFilter = Depends(),
    db: Session = Depends(get_db)
) -> List[ConsensusInDB]:
    """List consensus records with filters."""
    repository = ConsensusRepository(db)
    return repository.list_consensus(filters)

@router.patch("/{task_id}", response_model=ConsensusInDB)
def update_consensus(
    task_id: str,
    consensus_update: ConsensusUpdate,
    db: Session = Depends(get_db)
) -> ConsensusInDB:
    """Update consensus record."""
    repository = ConsensusRepository(db)
    consensus = repository.update(task_id, consensus_update)
    if not consensus:
        raise HTTPException(
            status_code=404,
            detail=f"Consensus not found for task {task_id}"
        )
    return consensus

@router.delete("/{task_id}", status_code=204)
def delete_consensus(
    task_id: str,
    db: Session = Depends(get_db)
) -> None:
    """Delete consensus record."""
    repository = ConsensusRepository(db)
    if not repository.delete(task_id):
        raise HTTPException(
            status_code=404,
            detail=f"Consensus not found for task {task_id}"
        )

@router.get("/statistics/summary", response_model=ConsensusStatistics)
def get_consensus_statistics(
    db: Session = Depends(get_db)
) -> ConsensusStatistics:
    """Get consensus statistics."""
    repository = ConsensusRepository(db)
    return repository.get_statistics() 