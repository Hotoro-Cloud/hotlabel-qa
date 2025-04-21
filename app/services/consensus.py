from typing import Dict, Any, List, Tuple, Union, Optional
from app.models.validation import Validation
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.consensus import Consensus, ConsensusStatus
from app.core.exceptions import ServiceException
from app.schemas.consensus import ConsensusCreate, ConsensusUpdate

logger = logging.getLogger(__name__)

def calculate_consensus(
    validations: List[Validation]
) -> Tuple[Dict[str, Any], float]:
    """Calculate consensus from multiple validations
    
    Args:
        validations: List of validation models to analyze
        
    Returns:
        Tuple containing:
            - consensus_result: The agreed-upon result
            - agreement_level: The level of agreement (0.0 to 1.0)
    """
    if not validations:
        return {}, 0.0
    
    # Extract responses from validations
    responses = [v.response for v in validations if v.response is not None]
    
    if not responses:
        return {}, 0.0
    
    # The consensus approach depends on the type of responses
    sample_response = responses[0]
    
    if isinstance(sample_response, str):
        return _calculate_text_consensus(responses)
    elif isinstance(sample_response, dict):
        return _calculate_dict_consensus(responses)
    elif isinstance(sample_response, list):
        return _calculate_list_consensus(responses)
    else:
        # Simple consensus for basic types (int, bool, etc.)
        return _calculate_simple_consensus(responses)

def _calculate_text_consensus(responses: List[str]) -> Tuple[str, float]:
    """Calculate consensus for text responses"""
    # Normalize responses
    normalized_responses = [r.strip().lower() for r in responses if isinstance(r, str)]
    
    if not normalized_responses:
        return "", 0.0
    
    # Count frequency of each normalized response
    from collections import Counter
    response_counts = Counter(normalized_responses)
    
    # Find most common response and its count
    most_common = response_counts.most_common(1)[0]
    most_common_response, count = most_common
    
    # Calculate agreement level
    agreement_level = count / len(normalized_responses)
    
    return most_common_response, agreement_level

def _calculate_dict_consensus(responses: List[Dict]) -> Tuple[Dict[str, Any], float]:
    """Calculate consensus for dictionary responses"""
    # This would be a more sophisticated implementation in a real system
    # For now, we'll do a key-by-key majority vote
    
    if not responses:
        return {}, 0.0
    
    # Collect all keys from all responses
    all_keys = set()
    for response in responses:
        all_keys.update(response.keys())
    
    consensus_result = {}
    key_agreement_levels = []
    
    # For each key, find the most common value
    for key in all_keys:
        # Collect all values for this key
        key_values = []
        for response in responses:
            if key in response:
                key_values.append(str(response[key]))  # Convert to string for comparison
        
        if not key_values:
            continue
        
        # Find the most common value
        from collections import Counter
        value_counts = Counter(key_values)
        most_common = value_counts.most_common(1)[0]
        most_common_value, count = most_common
        
        # Calculate agreement level for this key
        key_agreement = count / len(responses)
        key_agreement_levels.append(key_agreement)
        
        # Add to consensus result if agreement is sufficient
        if key_agreement > 0.5:  # More than 50% agreement
            try:
                # Try to convert back to original type
                if most_common_value.lower() == 'true':
                    consensus_result[key] = True
                elif most_common_value.lower() == 'false':
                    consensus_result[key] = False
                elif most_common_value.isdigit():
                    consensus_result[key] = int(most_common_value)
                elif most_common_value.replace('.', '', 1).isdigit():
                    consensus_result[key] = float(most_common_value)
                else:
                    consensus_result[key] = most_common_value
            except:
                consensus_result[key] = most_common_value
    
    # Calculate overall agreement level as average of key agreements
    overall_agreement = sum(key_agreement_levels) / len(key_agreement_levels) if key_agreement_levels else 0.0
    
    return consensus_result, overall_agreement

def _calculate_list_consensus(responses: List[List]) -> Tuple[List, float]:
    """Calculate consensus for list responses"""
    # This is a simplified implementation
    # In a real system, this would need to handle more complex cases
    
    if not responses:
        return [], 0.0
    
    # Flatten all items from all lists
    all_items = []
    for response in responses:
        if isinstance(response, list):
            all_items.extend(str(item) for item in response)  # Convert to strings for comparison
    
    if not all_items:
        return [], 0.0
    
    # Count frequency of each item
    from collections import Counter
    item_counts = Counter(all_items)
    
    # Include items that appear in at least half of the responses
    consensus_items = []
    threshold = len(responses) / 2
    for item, count in item_counts.items():
        if count >= threshold:
            # Try to convert back to original type when adding to consensus
            try:
                if item.lower() == 'true':
                    consensus_items.append(True)
                elif item.lower() == 'false':
                    consensus_items.append(False)
                elif item.isdigit():
                    consensus_items.append(int(item))
                elif item.replace('.', '', 1).isdigit():
                    consensus_items.append(float(item))
                else:
                    consensus_items.append(item)
            except:
                consensus_items.append(item)
    
    # Calculate agreement level
    # This is a simplification - real implementation would be more sophisticated
    agreement_level = len(consensus_items) / len(item_counts) if item_counts else 0.0
    
    return consensus_items, agreement_level

def _calculate_simple_consensus(responses: List[Any]) -> Tuple[Any, float]:
    """Calculate consensus for simple types (int, bool, etc.)"""
    if not responses:
        return None, 0.0
    
    # Count frequency of each response
    from collections import Counter
    response_counts = Counter(str(r) for r in responses)  # Convert to strings for counting
    
    # Find most common response and its count
    most_common = response_counts.most_common(1)[0]
    most_common_response_str, count = most_common
    
    # Convert back to original type if possible
    try:
        if most_common_response_str.lower() == 'true':
            most_common_response = True
        elif most_common_response_str.lower() == 'false':
            most_common_response = False
        elif most_common_response_str.isdigit():
            most_common_response = int(most_common_response_str)
        elif most_common_response_str.replace('.', '', 1).isdigit():
            most_common_response = float(most_common_response_str)
        else:
            most_common_response = most_common_response_str
    except:
        most_common_response = most_common_response_str
    
    # Calculate agreement level
    agreement_level = count / len(responses)
    
    return most_common_response, agreement_level

class ConsensusService:
    def __init__(self, db: Session):
        self.db = db

    async def create_consensus(self, task_id: str) -> Consensus:
        """Create a new consensus record for a task."""
        # Check if consensus already exists
        existing = self.db.query(Consensus).filter(Consensus.task_id == task_id).first()
        if existing:
            raise ServiceException(
                message=f"Consensus already exists for task {task_id}",
                status_code=400,
                details={"error": "consensus_exists"}
            )

        # Get all validations for the task
        validations = self.db.query(Validation).filter(
            Validation.task_id == task_id
        ).all()

        if not validations:
            raise ServiceException(
                message=f"No validations found for task {task_id}",
                status_code=404,
                details={"error": "no_validations"}
            )

        # Calculate agreement score
        agreement_score = await self.calculate_agreement_score(task_id)

        consensus = Consensus(
            task_id=task_id,
            status=ConsensusStatus.PENDING,
            agreement_score=agreement_score,
            validator_count=len(validations)
        )

        self.db.add(consensus)
        self.db.commit()
        self.db.refresh(consensus)

        return consensus

    async def get_consensus(self, task_id: str) -> Consensus:
        """Get consensus by task ID."""
        consensus = self.db.query(Consensus).filter(
            Consensus.task_id == task_id
        ).first()

        if not consensus:
            raise ServiceException(
                message=f"Consensus not found for task {task_id}",
                status_code=404,
                details={"error": "consensus_not_found"}
            )

        return consensus

    async def update_consensus_status(
        self, task_id: str, status: ConsensusStatus
    ) -> Consensus:
        """Update consensus status."""
        consensus = await self.get_consensus(task_id)
        consensus.status = status
        self.db.commit()
        self.db.refresh(consensus)
        return consensus

    async def list_consensus(
        self,
        status: Optional[ConsensusStatus] = None,
        min_agreement: Optional[float] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Consensus]:
        """List consensus records with optional filters."""
        query = self.db.query(Consensus)

        if status:
            query = query.filter(Consensus.status == status)
        if min_agreement is not None:
            query = query.filter(Consensus.agreement_score >= min_agreement)

        return query.limit(limit).offset(offset).all()

    async def delete_consensus(self, task_id: str) -> None:
        """Delete a consensus record."""
        result = self.delete_consensus_sync(task_id)
        if not result:
            raise ServiceException(
                message=f"Consensus not found for task {task_id}",
                status_code=404,
                details={"error": "consensus_not_found"}
            )

    async def calculate_agreement_score(self, task_id: str) -> float:
        """Calculate agreement score based on validations."""
        validations = self.db.query(Validation).filter(
            Validation.task_id == task_id
        ).all()

        if not validations:
            return 0.0

        # Count validations by status
        status_counts = {}
        for validation in validations:
            status_counts[validation.status] = status_counts.get(validation.status, 0) + 1

        # Find the most common status
        max_count = max(status_counts.values())
        total_validations = len(validations)

        # Calculate agreement score
        return max_count / total_validations if total_validations > 0 else 0.0

    async def get_consensus_statistics(self) -> Dict[str, Any]:
        """Get statistics about consensus records."""
        return self.get_consensus_statistics_sync()

    def create_consensus_sync(self, task_id_or_data) -> Consensus:
        """Create a new consensus record."""
        if isinstance(task_id_or_data, str):
            # If a string is provided, assume it's a task_id
            task_id = task_id_or_data
            import uuid
            db_consensus = Consensus(
                id=str(uuid.uuid4()),
                task_id=task_id,
                status=ConsensusStatus.PENDING,
                agreement_score=0.0,
                validator_count=0
            )
        else:
            # Otherwise, assume it's a ConsensusCreate object
            consensus_data = task_id_or_data
            db_consensus = Consensus(**consensus_data.model_dump())
            
        self.db.add(db_consensus)
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus
    
    def get_consensus_by_task_id(self, task_id: str) -> Optional[Consensus]:
        """Get consensus by task ID."""
        return self.db.query(Consensus).filter(Consensus.task_id == task_id).first()
    
    def update_consensus(self, task_id: str, consensus_update: ConsensusUpdate) -> Optional[Consensus]:
        """Update consensus record."""
        db_consensus = self.get_consensus_by_task_id(task_id)
        if not db_consensus:
            return None
        
        update_data = consensus_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_consensus, field, value)
        
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus
    
    def delete_consensus_sync(self, task_id: str) -> bool:
        """Delete consensus record."""
        db_consensus = self.get_consensus_by_task_id(task_id)
        if not db_consensus:
            return False
        
        self.db.delete(db_consensus)
        self.db.commit()
        return True
    
    def get_consensus_statistics_sync(self) -> Dict[str, Any]:
        """Get consensus statistics."""
        from sqlalchemy import func
        
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
            "total_consensus": total,
            "status_distribution": status_distribution,
            "average_agreement": float(avg_agreement)
        }
    
    def check_and_update_consensus(self, task_id: str) -> Optional[Consensus]:
        """Check and update consensus for a task."""
        db_consensus = self.get_consensus_by_task_id(task_id)
        if not db_consensus:
            return None
        
        # Get all validations for this task
        validations = self.db.query(Validation).filter(
            Validation.task_id == task_id
        ).all()
        
        if not validations:
            return db_consensus
        
        # Calculate agreement score
        total_validations = len(validations)
        if total_validations < 2:
            # Need at least 2 validations to calculate agreement
            return db_consensus
        
        # Count how many validations agree with each other
        agreement_count = 0
        total_comparisons = 0
        
        for i in range(total_validations):
            for j in range(i + 1, total_validations):
                total_comparisons += 1
                if validations[i].response == validations[j].response:
                    agreement_count += 1
        
        # Calculate agreement score
        agreement_score = agreement_count / total_comparisons if total_comparisons > 0 else 0.0
        
        # Update consensus
        update_data = {
            "agreement_score": agreement_score,
            "validator_count": total_validations
        }
        
        # Update status based on agreement score
        if agreement_score >= 0.8:  # 80% agreement threshold
            update_data["status"] = ConsensusStatus.APPROVED
        elif agreement_score < 0.5:  # Less than 50% agreement
            update_data["status"] = ConsensusStatus.REJECTED
        else:
            update_data["status"] = ConsensusStatus.REVIEW
        
        # Apply updates
        for field, value in update_data.items():
            setattr(db_consensus, field, value)
        
        self.db.commit()
        self.db.refresh(db_consensus)
        return db_consensus
