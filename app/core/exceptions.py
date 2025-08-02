"""Custom exceptions and exception handling utilities.

This module provides custom exception classes and utilities for handling exceptions
in a consistent way across the application.
"""
from typing import Dict, Any, Optional, Type, List, Union
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.api.schemas.common import create_error_response, create_validation_error_response

logger = logging.getLogger(__name__)

class AppException(Exception):
    """Base exception for all application exceptions.
    
    This class serves as the base for all custom exceptions in the application.
    It includes a status code and a message that can be used to generate a response.
    
    Attributes:
        message: A human-readable error message.
        status_code: The HTTP status code to return.
        detail: Additional details about the error.
    """
    def __init__(
        self, 
        message: str, 
        status_code: int = 500, 
        detail: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)

class NotFoundException(AppException):
    """Exception raised when a resource is not found.
    
    Attributes:
        message: A human-readable error message.
        resource_type: The type of resource that was not found.
        resource_id: The ID of the resource that was not found.
    """
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None, 
        resource_id: Optional[Union[str, int]] = None
    ):
        detail = {}
        if resource_type:
            detail["resource_type"] = resource_type
        if resource_id:
            detail["resource_id"] = resource_id
        super().__init__(message, status_code=404, detail=detail)

class BadRequestException(AppException):
    """Exception raised when a request is invalid.
    
    Attributes:
        message: A human-readable error message.
        errors: A list of validation errors.
    """
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        detail = {"errors": errors} if errors else {}
        super().__init__(message, status_code=400, detail=detail)

class UnauthorizedException(AppException):
    """Exception raised when a user is not authorized.
    
    Attributes:
        message: A human-readable error message.
    """
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)

class ForbiddenException(AppException):
    """Exception raised when a user is forbidden from accessing a resource.
    
    Attributes:
        message: A human-readable error message.
    """
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, status_code=403)

class ConflictException(AppException):
    """Exception raised when there is a conflict with the current state of the resource.
    
    Attributes:
        message: A human-readable error message.
        resource_type: The type of resource that has a conflict.
        resource_id: The ID of the resource that has a conflict.
    """
    def __init__(
        self, 
        message: str, 
        resource_type: Optional[str] = None, 
        resource_id: Optional[Union[str, int]] = None
    ):
        detail = {}
        if resource_type:
            detail["resource_type"] = resource_type
        if resource_id:
            detail["resource_id"] = resource_id
        super().__init__(message, status_code=409, detail=detail)

class ValidationException(AppException):
    """Exception raised when validation fails.
    
    Attributes:
        message: A human-readable error message.
        errors: A list of validation errors.
    """
    def __init__(self, message: str, errors: Optional[List[Dict[str, Any]]] = None):
        detail = {"errors": errors} if errors else {}
        super().__init__(message, status_code=422, detail=detail)

class DatabaseException(AppException):
    """Exception raised when there is a database error.
    
    Attributes:
        message: A human-readable error message.
        original_exception: The original exception that was raised.
    """
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        detail = {}
        if original_exception:
            detail["original_exception"] = str(original_exception)
        super().__init__(message, status_code=503, detail=detail)

class LLMException(AppException):
    """Exception raised when there is an error with the LLM.
    
    Attributes:
        message: A human-readable error message.
        original_exception: The original exception that was raised.
    """
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        detail = {}
        if original_exception:
            detail["original_exception"] = str(original_exception)
        super().__init__(message, status_code=500, detail=detail)

class SSEException(AppException):
    """Exception raised when there is an error with SSE.
    
    Attributes:
        message: A human-readable error message.
        original_exception: The original exception that was raised.
    """
    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        detail = {}
        if original_exception:
            detail["original_exception"] = str(original_exception)
        super().__init__(message, status_code=500, detail=detail)

# Exception handlers
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle application exceptions.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        A JSON response with the error details.
    """
    logger.error(f"AppException: {exc.message}", exc_info=True)
    
    # Determine error code based on exception type
    error_code = exc.__class__.__name__.replace("Exception", "").upper()
    
    error_response = create_error_response(
        message=exc.message,
        error_code=error_code,
        details=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle validation errors.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        A JSON response with the validation errors.
    """
    logger.error(f"ValidationError: {exc.errors()}", exc_info=True)
    
    error_response = create_validation_error_response(
        message="Request validation failed",
        details=exc.errors()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )

async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic validation errors.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        A JSON response with the validation errors.
    """
    logger.error(f"PydanticValidationError: {exc.errors()}", exc_info=True)
    
    error_response = create_validation_error_response(
        message="Data validation failed",
        details=exc.errors()
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump()
    )

async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all other exceptions.
    
    Args:
        request: The request that caused the exception.
        exc: The exception that was raised.
        
    Returns:
        A JSON response with a generic error message.
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    error_response = create_error_response(
        message="Internal server error",
        error_code="INTERNAL_SERVER_ERROR",
        details={
            "exception_type": exc.__class__.__name__,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    # Use safe serialization to avoid datetime serialization issues
    try:
        content = error_response.model_dump()
    except Exception:
        # Fallback to a simple error message if model serialization fails
        content = {
            "success": False,
            "message": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content
    )

def register_exception_handlers(app) -> None:
    """Register exception handlers with the FastAPI application.
    
    Args:
        app: The FastAPI application.
    """
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, pydantic_validation_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)