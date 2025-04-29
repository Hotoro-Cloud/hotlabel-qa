from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.services.validation_service import ValidationService
from app.db.repositories.golden_set_repository import GoldenSetRepository
from app.db.repositories.consensus_repository import ConsensusRepository
from app.db.repositories.validator_repository import ValidatorRepository
from app.schemas.golden_set import GoldenSetCreate, GoldenSetResponse
from app.schemas.consensus import ConsensusResponse
from app.schemas.validator import ValidatorCreate, ValidatorResponse
from app.api.deps import get_validation_service, get_golden_set_repository, get_consensus_repository, get_validator_repository
from app.core.exceptions import ResourceNotFound
from app.db.session import get_db

admin_router = APIRouter(prefix="/api/v1/admin", tags=["admin"])

# Validator management
@admin_router.get("/validators", response_model=List[ValidatorResponse])
async def get_validators(
    validator_repo: ValidatorRepository = Depends(get_validator_repository)
) -> Any:
    """
    Get all validators.
    """
    try:
        validators = validator_repo.get_all()
        return validators
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@admin_router.post("/validators", response_model=ValidatorResponse)
async def create_validator(
    validator: ValidatorCreate,
    validator_repo: ValidatorRepository = Depends(get_validator_repository)
) -> Any:
    """
    Create a new validator.
    """
    try:
        result = validator_repo.create(validator)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

# Golden Set management
@admin_router.post("/golden-sets", response_model=GoldenSetResponse)
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

@admin_router.get("/golden-sets/{golden_set_id}", response_model=GoldenSetResponse)
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

@admin_router.get("/golden-sets", response_model=List[GoldenSetResponse])
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
            # Get all golden sets
            results = golden_set_repo.get_all()
        return [GoldenSetResponse.from_orm(result) for result in results]
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

# Consensus group management
@admin_router.get("/consensus/{task_id}", response_model=ConsensusResponse)
def get_consensus(
    task_id: str,
    db: Session = Depends(get_db)
) -> ConsensusResponse:
    """Get consensus by task ID."""
    service = ValidationService(db)
    result = service.get_consensus_by_task_id(task_id)
    if not result:
        raise ResourceNotFound("Consensus", task_id)
    return ConsensusResponse.from_orm(result)

@admin_router.post("/consensus/{task_id}/check", response_model=ConsensusResponse)
def check_consensus(
    task_id: str,
    db: Session = Depends(get_db)
) -> ConsensusResponse:
    """Check and update consensus for a task."""
    service = ValidationService(db)
    result = service.check_and_update_consensus(task_id)
    if not result:
        raise ResourceNotFound("Consensus", task_id)
    return ConsensusResponse.from_orm(result)
