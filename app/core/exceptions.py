from typing import Dict, Any, Optional

class ServiceException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(ServiceException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="validation_error",
            message=message,
            status_code=400,
            details=details
        )

class ResourceNotFound(ServiceException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="resource_not_found",
            message=f"{resource_type} with ID {resource_id} not found",
            status_code=404,
            details={
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        )

class ExternalServiceError(ServiceException):
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="external_service_error",
            message=f"Error communicating with {service}: {message}",
            status_code=502,
            details=details or {}
        )

class InternalServerError(ServiceException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            code="internal_server_error",
            message=message,
            status_code=500,
            details=details or {}
        )
