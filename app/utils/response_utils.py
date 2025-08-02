"""Response formatting utilities."""
from typing import Any, Dict, List, Optional, Type, TypeVar
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.api.schemas.common import (
    SuccessResponse,
    ErrorResponse,
    ValidationErrorResponse,
    ListResponse,
    PaginatedResponse,
    create_success_response,
    create_error_response,
    create_validation_error_response,
    create_list_response,
    create_paginated_response,
)

T = TypeVar('T', bound=BaseModel)

class ResponseFormatter:
    """Utility class for formatting API responses."""
    
    @staticmethod
    def success(
        data: Any = None,
        message: str = "Success",
        status_code: int = status.HTTP_200_OK,
    ) -> JSONResponse:
        """Format a success response."""
        response = create_success_response(data=data, message=message)
        return JSONResponse(
            content=response.model_dump(),
            status_code=status_code
        )
    
    @staticmethod
    def created(
        data: Any = None,
        message: str = "Resource created successfully",
    ) -> JSONResponse:
        """Format a created response."""
        return ResponseFormatter.success(
            data=data,
            message=message,
            status_code=status.HTTP_201_CREATED
        )
    
    @staticmethod
    def updated(
        data: Any = None,
        message: str = "Resource updated successfully",
    ) -> JSONResponse:
        """Format an updated response."""
        return ResponseFormatter.success(
            data=data,
            message=message,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def deleted(
        message: str = "Resource deleted successfully",
    ) -> JSONResponse:
        """Format a deleted response."""
        return ResponseFormatter.success(
            data=None,
            message=message,
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def list_response(
        data: List[Any],
        message: str = "Success",
    ) -> JSONResponse:
        """Format a list response."""
        response = create_list_response(data=data, message=message)
        return JSONResponse(
            content=response.model_dump(),
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def paginated_response(
        data: List[Any],
        page: int,
        per_page: int,
        total: int,
        message: str = "Success",
    ) -> JSONResponse:
        """Format a paginated response."""
        response = create_paginated_response(
            data=data,
            page=page,
            per_page=per_page,
            total=total,
            message=message
        )
        return JSONResponse(
            content=response.model_dump(),
            status_code=status.HTTP_200_OK
        )
    
    @staticmethod
    def error(
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Format an error response."""
        response = create_error_response(
            message=message,
            error_code=error_code,
            details=details
        )
        return JSONResponse(
            content=response.model_dump(),
            status_code=status_code
        )
    
    @staticmethod
    def not_found(
        message: str = "Resource not found",
        error_code: str = "NOT_FOUND",
    ) -> JSONResponse:
        """Format a not found response."""
        return ResponseFormatter.error(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code=error_code
        )
    
    @staticmethod
    def bad_request(
        message: str = "Bad request",
        error_code: str = "BAD_REQUEST",
        details: Optional[Dict[str, Any]] = None,
    ) -> JSONResponse:
        """Format a bad request response."""
        return ResponseFormatter.error(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code=error_code,
            details=details
        )
    
    @staticmethod
    def unauthorized(
        message: str = "Unauthorized",
        error_code: str = "UNAUTHORIZED",
    ) -> JSONResponse:
        """Format an unauthorized response."""
        return ResponseFormatter.error(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code=error_code
        )
    
    @staticmethod
    def forbidden(
        message: str = "Forbidden",
        error_code: str = "FORBIDDEN",
    ) -> JSONResponse:
        """Format a forbidden response."""
        return ResponseFormatter.error(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code=error_code
        )
    
    @staticmethod
    def validation_error(
        message: str = "Validation failed",
        details: Optional[List[Dict[str, Any]]] = None,
    ) -> JSONResponse:
        """Format a validation error response."""
        response = create_validation_error_response(
            message=message,
            details=details
        )
        return JSONResponse(
            content=response.model_dump(),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )
    
    @staticmethod
    def internal_server_error(
        message: str = "Internal server error",
        error_code: str = "INTERNAL_SERVER_ERROR",
    ) -> JSONResponse:
        """Format an internal server error response."""
        return ResponseFormatter.error(
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code=error_code
        )

# Convenience functions for common responses
def success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    """Create a success response."""
    return ResponseFormatter.success(data=data, message=message)

def created_response(data: Any = None, message: str = "Resource created successfully") -> JSONResponse:
    """Create a created response."""
    return ResponseFormatter.created(data=data, message=message)

def updated_response(data: Any = None, message: str = "Resource updated successfully") -> JSONResponse:
    """Create an updated response."""
    return ResponseFormatter.updated(data=data, message=message)

def deleted_response(message: str = "Resource deleted successfully") -> JSONResponse:
    """Create a deleted response."""
    return ResponseFormatter.deleted(message=message)

def list_response(data: List[Any], message: str = "Success") -> JSONResponse:
    """Create a list response."""
    return ResponseFormatter.list_response(data=data, message=message)

def paginated_response(
    data: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: str = "Success"
) -> JSONResponse:
    """Create a paginated response."""
    return ResponseFormatter.paginated_response(
        data=data,
        page=page,
        per_page=per_page,
        total=total,
        message=message
    )

def error_response(
    message: str,
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> JSONResponse:
    """Create an error response."""
    return ResponseFormatter.error(
        message=message,
        status_code=status_code,
        error_code=error_code,
        details=details
    )

def not_found_response(message: str = "Resource not found") -> JSONResponse:
    """Create a not found response."""
    return ResponseFormatter.not_found(message=message)

def bad_request_response(
    message: str = "Bad request",
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a bad request response."""
    return ResponseFormatter.bad_request(message=message, details=details)

def validation_error_response(
    message: str = "Validation failed",
    details: Optional[List[Dict[str, Any]]] = None
) -> JSONResponse:
    """Create a validation error response."""
    return ResponseFormatter.validation_error(message=message, details=details)