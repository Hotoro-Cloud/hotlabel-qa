from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.consensus import Consensus, ConsensusStatus
from app.schemas.consensus import ConsensusCreate, ConsensusUpdate, ConsensusFilter

class ConsensusRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, consensus_create: ConsensusCreate) -> Consensus:
        """Create a new consensus record."""
        db_consensus = Consensus(**consensus_create.model_dump())
        self.db.add(db_consensus)
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus

    def get_by_task_id(self, task_id: str) -> Optional[Consensus]:
        """Get consensus by task ID."""
        return self.db.query(Consensus).filter(Consensus.task_id == task_id).first()

    def list_consensus(self, filters: ConsensusFilter) -> List[Consensus]:
        """List consensus records with filters."""
        query = self.db.query(Consensus)

        if filters.status:
            query = query.filter(Consensus.status == filters.status)
        if filters.min_agreement_score is not None:
            query = query.filter(Consensus.agreement_score >= filters.min_agreement_score)

        return query.offset(filters.skip).limit(filters.limit).all()

    def update(self, task_id: str, consensus_update: ConsensusUpdate) -> Optional[Consensus]:
        """Update consensus record."""
        db_consensus = self.get_by_task_id(task_id)
        if not db_consensus:
            return None

        update_data = consensus_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_consensus, field, value)

        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus

    def delete(self, task_id: str) -> bool:
        """Delete consensus record."""
        db_consensus = self.get_by_task_id(task_id)
        if not db_consensus:
            return False

        self.db.delete(db_consensus)
        self.db.commit()
        return True

    def get_statistics(self) -> dict:
        """Get consensus statistics."""
        total = self.db.query(func.count(Consensus.task_id)).scalar()
        
        status_distribution = {}
        for status in ConsensusStatus:
            count = self.db.query(func.count(Consensus.task_id)).filter(
                Consensus.status == status
            ).scalar()
            status_distribution[status] = count

        avg_agreement = self.db.query(
            func.avg(Consensus.agreement_score)
        ).scalar() or 0.0

        return {
            "total_count": total,
            "status_distribution": status_distribution,
            "average_agreement_score": float(avg_agreement)
        }
