from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.consensus import ConsensusGroup, ConsensusStatus
from app.models.validation import Validation
from app.schemas.consensus import ConsensusGroupCreate

class ConsensusRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, consensus_data: ConsensusGroupCreate) -> ConsensusGroup:
        db_consensus = ConsensusGroup(
            task_id=consensus_data.task_id,
            required_validations=consensus_data.required_validations,
            agreement_threshold=consensus_data.agreement_threshold
        )
        self.db.add(db_consensus)
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus
    
    def get_by_id(self, consensus_id: str) -> Optional[ConsensusGroup]:
        return self.db.query(ConsensusGroup).filter(ConsensusGroup.id == consensus_id).first()
    
    def get_by_task_id(self, task_id: str) -> Optional[ConsensusGroup]:
        return self.db.query(ConsensusGroup).filter(ConsensusGroup.task_id == task_id).first()
    
    def list_pending_groups(self) -> List[ConsensusGroup]:
        return self.db.query(ConsensusGroup)\
            .filter(ConsensusGroup.status.in_([ConsensusStatus.PENDING, ConsensusStatus.IN_PROGRESS]))\
            .all()
    
    def update(self, consensus_id: str, update_data: Dict[str, Any]) -> Optional[ConsensusGroup]:
        db_consensus = self.get_by_id(consensus_id)
        if not db_consensus:
            return None
        
        for key, value in update_data.items():
            setattr(db_consensus, key, value)
        
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus
    
    def add_validation(self, consensus_id: str, validation: Validation) -> Optional[ConsensusGroup]:
        db_consensus = self.get_by_id(consensus_id)
        if not db_consensus:
            return None
        
        # Update validation with consensus group ID
        validation.consensus_group_id = consensus_id
        
        # Update consensus group status
        if db_consensus.status == ConsensusStatus.PENDING:
            db_consensus.status = ConsensusStatus.IN_PROGRESS
        
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus
    
    def get_validations(self, consensus_id: str) -> List[Validation]:
        return self.db.query(Validation)\
            .filter(Validation.consensus_group_id == consensus_id)\
            .all()
    
    def check_and_update_consensus(self, consensus_id: str) -> Optional[ConsensusGroup]:
        db_consensus = self.get_by_id(consensus_id)
        if not db_consensus:
            return None
        
        validations = self.get_validations(consensus_id)
        validation_count = len(validations)
        
        # Check if we have enough validations to determine consensus
        if validation_count >= db_consensus.required_validations:
            # Implement consensus calculation logic here
            # This is a simplified example - actual implementation would be more complex
            
            # For demonstration: calculate average of all validations
            # In reality, this would be a more sophisticated algorithm comparing responses
            from app.services.consensus import calculate_consensus
            consensus_result, agreement_level = calculate_consensus(validations)
            
            if agreement_level >= db_consensus.agreement_threshold:
                db_consensus.status = ConsensusStatus.COMPLETED
                db_consensus.consensus_result = consensus_result
                db_consensus.agreement_level = agreement_level
                db_consensus.completed_at = import_module('sqlalchemy.sql').func.now()
            elif validation_count >= db_consensus.required_validations * 2:  # If we have twice the required validations but still no consensus
                db_consensus.status = ConsensusStatus.FAILED
            
            self.db.commit()
            self.db.refresh(db_consensus)
        
        return db_consensus
