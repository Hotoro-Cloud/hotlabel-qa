from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.validation_service import ValidationService
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.api.deps import get_validation_service
from app.core.exceptions import ResourceNotFound, ValidationError

validation_router = APIRouter(prefix="/api/v1/validation", tags=["validation"])

@validation_router.post("", response_model=ValidationResponse, status_code=201)
async def validate_label(validation_data: dict, service: ValidationService = Depends(get_validation_service)) -> Any:
    """
    Validate a submitted label.
    
    This endpoint analyzes the submitted response to determine its quality and confidence level.
    """
    try:
        # Create a validation directly
        result = await service.create_validation(validation_data)
        # Convert to response model
        return service._to_response_model(result)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={
            "code": "validation_error",
            "message": str(e),
            "details": {"field": "status"}
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@validation_router.get("/{validation_id}", response_model=ValidationResponse)
async def get_validation(validation_id: str, service: ValidationService = Depends(get_validation_service)) -> Any:
    """
    Get validation details by ID.
    """
    try:
        result = await service.get_validation(validation_id)
        return result
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": "resource_not_found",
            "message": str(e),
            "details": {"resource_id": validation_id}
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@validation_router.get("", response_model=List[ValidationResponse])
async def list_validations(
    status: str = Query(None, description="Filter by validation status"),
    validator_id: str = Query(None, description="Filter by validator ID"),
    service: ValidationService = Depends(get_validation_service)
) -> Any:
    """
    List validations with optional filters.
    """
    try:
        validations = await service.list_validations(status=status, validator_id=validator_id)
        return [service._to_response_model(validation) for validation in validations]
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@validation_router.patch("/{validation_id}/status", response_model=ValidationResponse)
async def update_validation_status(
    validation_id: str,
    update_data: dict,
    service: ValidationService = Depends(get_validation_service)
) -> Any:
    """
    Update validation status.
    """
    try:
        from app.models.validation import ValidationStatus
        status = ValidationStatus(update_data.get("status"))
        result = await service.update_validation_status(validation_id, status)
        return service._to_response_model(result)
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": "resource_not_found",
            "message": str(e),
            "details": {"resource_id": validation_id}
        })
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={
            "code": "validation_error",
            "message": str(e),
            "details": {"field": "status"}
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })

@validation_router.get("/results/{result_id}", response_model=ValidationResponse)
async def get_validation_by_result(result_id: str, service: ValidationService = Depends(get_validation_service)) -> Any:
    """
    Get validation details by result ID.
    """
    try:
        result = await service.get_validation_by_result(result_id)
        return result
    except ResourceNotFound as e:
        raise HTTPException(status_code=404, detail={
            "code": "resource_not_found",
            "message": str(e),
            "details": {"resource_id": result_id}
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail={
            "code": "internal_error",
            "message": "An unexpected error occurred",
            "details": {"error": str(e)}
        })
