from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.validation_service import ValidationService
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.api.deps import get_validation_service
from app.core.exceptions import ResourceNotFound, ValidationError

router = APIRouter(prefix="/quality", tags=["validation"])

@router.post("/validate", response_model=ValidationResponse)
async def validate_label(request: ValidationRequest, service: ValidationService = Depends(get_validation_service)) -> Any:
    """
    Validate a submitted label.
    
    This endpoint analyzes the submitted response to determine its quality and confidence level.
    """
    try:
        result = await service.validate_submission(request)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail={
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

@router.get("/validations/{validation_id}", response_model=ValidationResponse)
async def get_validation(validation_id: str, service: ValidationService = Depends(get_validation_service)) -> Any:
    """
    Get validation details by ID.
    """
    try:
        result = await service.get_validation(validation_id)
        return result
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

@router.get("/results/{result_id}", response_model=ValidationResponse)
async def get_validation_by_result(result_id: str, service: ValidationService = Depends(get_validation_service)) -> Any:
    """
    Get validation details by result ID.
    """
    try:
        result = await service.get_validation_by_result(result_id)
        return result
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
