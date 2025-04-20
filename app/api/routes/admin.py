from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks

from app.services.validation_service import ValidationService
from app.db.repositories.golden_set_repository import GoldenSetRepository
from app.db.repositories.consensus_repository import ConsensusRepository
from app.schemas.golden_set import GoldenSetCreate, GoldenSetResponse
from app.schemas.consensus import ConsensusGroupResponse
from app.api.deps import get_validation_service, get_golden_set_repository, get_consensus_repository
from app.core.exceptions import ResourceNotFound

router = APIRouter(prefix="/admin", tags=["admin"])

# Golden Set management
@router.post("/golden-sets", response_model=GoldenSetResponse)
async def create_golden_set(
    golden_set: GoldenSetCreate,
    golden_set_repo: GoldenSetRepository = Depends(get_golden_set_repository)
) -> Any:
    """
    Create a new golden set item.
    
    Golden sets are used as known-good examples for validation.
    """
    try:
        result = golden_set_repo.create(golden_set)
        return GoldenSetResponse.from_orm(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@router.get("/golden-sets/{golden_set_id}", response_model=GoldenSetResponse)
async def get_golden_set(
    golden_set_id: str,
    golden_set_repo: GoldenSetRepository = Depends(get_golden_set_repository)
) -> Any:
    """
    Get a golden set item by ID.
    """
    try:
        result = golden_set_repo.get_by_id(golden_set_id)
        if not result:
            raise ResourceNotFound("GoldenSet", golden_set_id)
        return GoldenSetResponse.from_orm(result)
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@router.get("/golden-sets", response_model=List[GoldenSetResponse])
async def list_golden_sets(
    category: Optional[str] = None,
    golden_set_repo: GoldenSetRepository = Depends(get_golden_set_repository)
) -> Any:
    """
    List golden sets, optionally filtered by category.
    """
    try:
        if category:
            results = golden_set_repo.list_by_category(category)
        else:
            # This would need a list_all method in a real implementation
            results = []
        return [GoldenSetResponse.from_orm(result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

# Consensus group management
@router.get("/consensus-groups/{consensus_id}", response_model=ConsensusGroupResponse)
async def get_consensus_group(
    consensus_id: str,
    consensus_repo: ConsensusRepository = Depends(get_consensus_repository)
) -> Any:
    """
    Get a consensus group by ID.
    """
    try:
        result = consensus_repo.get_by_id(consensus_id)
        if not result:
            raise ResourceNotFound("ConsensusGroup", consensus_id)
            
        # Add validation count for the response
        validations = consensus_repo.get_validations(consensus_id)
        response = ConsensusGroupResponse.from_orm(result)
        response.validation_count = len(validations)
        
        return response
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@router.post("/consensus-groups/{consensus_id}/check", response_model=ConsensusGroupResponse)
async def check_consensus_group(
    consensus_id: str,
    background_tasks: BackgroundTasks,
    consensus_repo: ConsensusRepository = Depends(get_consensus_repository)
) -> Any:
    """
    Check and update a consensus group status.
    """
    try:
        # Run the consensus check in the background
        def check_consensus():
            consensus_repo.check_and_update_consensus(consensus_id)
        
        background_tasks.add_task(check_consensus)
        
        # Return the current status
        result = consensus_repo.get_by_id(consensus_id)
        if not result:
            raise ResourceNotFound("ConsensusGroup", consensus_id)
            
        # Add validation count for the response
        validations = consensus_repo.get_validations(consensus_id)
        response = ConsensusGroupResponse.from_orm(result)
        response.validation_count = len(validations)
        
        return response
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": e.code,
            "message": e.message,
            "details": e.details
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })
