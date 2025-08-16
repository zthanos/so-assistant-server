"""Comprehensive error handling utilities for API endpoints."""

from typing import Dict, Any, Type, Union
from fastapi import HTTPException
from app.core.exceptions import (
    AppException, NotFoundException, BadRequestException, ConflictException,
    ValidationException, DatabaseException, UnauthorizedException, ForbiddenException
)
from app.exceptions.systems_teams_exceptions import (
    SystemNotFoundException, TeamNotFoundException, DuplicateSystemException,
    DuplicateTeamException, InvalidDependencyException, CircularDependencyException,
    SystemValidationException, TeamValidationException, TeamMemberValidationException,
    SystemOperationException, TeamOperationException, SystemDependencyException
)


class APIErrorHandler:
    """Centralized error handling for API endpoints."""
    
    # Mapping of exception types to HTTP status codes
    EXCEPTION_STATUS_MAPPING: Dict[Type[Exception], int] = {
        # Core exceptions
        NotFoundException: 404,
        BadRequestException: 400,
        ConflictException: 409,
        ValidationException: 422,
        UnauthorizedException: 401,
        ForbiddenException: 403,
        DatabaseException: 503,
        
        # Systems and Teams specific exceptions
        SystemNotFoundException: 404,
        TeamNotFoundException: 404,
        DuplicateSystemException: 409,
        DuplicateTeamException: 409,
        InvalidDependencyException: 422,
        CircularDependencyException: 422,
        SystemValidationException: 422,
        TeamValidationException: 422,
        TeamMemberValidationException: 422,
        SystemOperationException: 500,
        TeamOperationException: 500,
        SystemDependencyException: 400,
    }
    
    @classmethod
    def handle_exception(cls, exception: Exception) -> HTTPException:
        """Convert application exceptions to HTTP exceptions.
        
        Args:
            exception: The exception to handle.
            
        Returns:
            HTTPException with appropriate status code and detail.
        """
        if isinstance(exception, AppException):
            # Use the exception's own status code if available
            status_code = getattr(exception, 'status_code', 500)
            
            # Create detailed error response
            error_code = exception.__class__.__name__.replace("Exception", "")
            # Convert camelCase to SNAKE_CASE
            import re
            error_code = re.sub('([a-z0-9])([A-Z])', r'\1_\2', error_code).upper()
            
            detail = {
                "message": exception.message,
                "error_code": error_code,
                "details": exception.detail if hasattr(exception, 'detail') else {}
            }
            
            return HTTPException(status_code=status_code, detail=detail)
        
        # For non-AppException types, use the mapping
        exception_type = type(exception)
        status_code = cls.EXCEPTION_STATUS_MAPPING.get(exception_type, 500)
        
        detail = {
            "message": str(exception),
            "error_code": exception_type.__name__.replace("Exception", "").upper(),
            "details": {}
        }
        
        return HTTPException(status_code=status_code, detail=detail)
    
    @classmethod
    def handle_systems_exceptions(cls, exception: Exception) -> HTTPException:
        """Handle systems-specific exceptions with enhanced error details.
        
        Args:
            exception: The exception to handle.
            
        Returns:
            HTTPException with systems-specific error details.
        """
        if isinstance(exception, (SystemNotFoundException, SystemOperationException)):
            return cls.handle_exception(exception)
        elif isinstance(exception, DuplicateSystemException):
            detail = {
                "message": exception.message,
                "error_code": "DUPLICATE_SYSTEM",
                "details": {
                    "resource_type": "System",
                    "conflict_type": "name_already_exists",
                    **exception.detail
                }
            }
            return HTTPException(status_code=409, detail=detail)
        elif isinstance(exception, InvalidDependencyException):
            detail = {
                "message": exception.message,
                "error_code": "INVALID_DEPENDENCIES",
                "details": {
                    "resource_type": "System",
                    "validation_type": "dependency_validation",
                    **exception.detail
                }
            }
            return HTTPException(status_code=422, detail=detail)
        elif isinstance(exception, CircularDependencyException):
            detail = {
                "message": exception.message,
                "error_code": "CIRCULAR_DEPENDENCY",
                "details": {
                    "resource_type": "System",
                    "validation_type": "circular_dependency_check",
                    **exception.detail
                }
            }
            return HTTPException(status_code=422, detail=detail)
        else:
            return cls.handle_exception(exception)
    
    @classmethod
    def handle_teams_exceptions(cls, exception: Exception) -> HTTPException:
        """Handle teams-specific exceptions with enhanced error details.
        
        Args:
            exception: The exception to handle.
            
        Returns:
            HTTPException with teams-specific error details.
        """
        if isinstance(exception, (TeamNotFoundException, TeamOperationException)):
            return cls.handle_exception(exception)
        elif isinstance(exception, DuplicateTeamException):
            detail = {
                "message": exception.message,
                "error_code": "DUPLICATE_TEAM",
                "details": {
                    "resource_type": "Team",
                    "conflict_type": "name_already_exists",
                    **exception.detail
                }
            }
            return HTTPException(status_code=409, detail=detail)
        elif isinstance(exception, TeamMemberValidationException):
            detail = {
                "message": exception.message,
                "error_code": "INVALID_TEAM_MEMBERS",
                "details": {
                    "resource_type": "Team",
                    "validation_type": "member_validation",
                    **exception.detail
                }
            }
            return HTTPException(status_code=422, detail=detail)
        elif isinstance(exception, TeamValidationException):
            detail = {
                "message": exception.message,
                "error_code": "TEAM_VALIDATION_ERROR",
                "details": {
                    "resource_type": "Team",
                    "validation_type": "general_validation",
                    **exception.detail
                }
            }
            return HTTPException(status_code=422, detail=detail)
        else:
            return cls.handle_exception(exception)


def handle_api_exceptions(func):
    """Decorator to handle API exceptions consistently.
    
    Args:
        func: The API endpoint function to wrap.
        
    Returns:
        Wrapped function with exception handling.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise APIErrorHandler.handle_exception(e)
    
    return wrapper


def handle_systems_api_exceptions(func):
    """Decorator to handle systems API exceptions with enhanced error details.
    
    Args:
        func: The systems API endpoint function to wrap.
        
    Returns:
        Wrapped function with systems-specific exception handling.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise APIErrorHandler.handle_systems_exceptions(e)
    
    return wrapper


def handle_teams_api_exceptions(func):
    """Decorator to handle teams API exceptions with enhanced error details.
    
    Args:
        func: The teams API endpoint function to wrap.
        
    Returns:
        Wrapped function with teams-specific exception handling.
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise APIErrorHandler.handle_teams_exceptions(e)
    
    return wrapper


# Utility functions for common error scenarios
def create_validation_error_detail(
    message: str,
    field_errors: Dict[str, str],
    resource_type: str = "Resource"
) -> Dict[str, Any]:
    """Create a standardized validation error detail.
    
    Args:
        message: The main error message.
        field_errors: Dictionary of field-specific errors.
        resource_type: The type of resource being validated.
        
    Returns:
        Standardized error detail dictionary.
    """
    return {
        "message": message,
        "error_code": "VALIDATION_ERROR",
        "details": {
            "resource_type": resource_type,
            "validation_type": "field_validation",
            "field_errors": field_errors
        }
    }


def create_not_found_error_detail(
    resource_type: str,
    resource_id: Union[str, int],
    message: str = None
) -> Dict[str, Any]:
    """Create a standardized not found error detail.
    
    Args:
        resource_type: The type of resource that was not found.
        resource_id: The ID of the resource that was not found.
        message: Optional custom message.
        
    Returns:
        Standardized error detail dictionary.
    """
    default_message = f"{resource_type} with ID {resource_id} not found"
    return {
        "message": message or default_message,
        "error_code": "NOT_FOUND",
        "details": {
            "resource_type": resource_type,
            "resource_id": resource_id
        }
    }


def create_conflict_error_detail(
    resource_type: str,
    conflict_field: str,
    conflict_value: str,
    message: str = None
) -> Dict[str, Any]:
    """Create a standardized conflict error detail.
    
    Args:
        resource_type: The type of resource with the conflict.
        conflict_field: The field that has the conflict.
        conflict_value: The value that causes the conflict.
        message: Optional custom message.
        
    Returns:
        Standardized error detail dictionary.
    """
    default_message = f"{resource_type} with {conflict_field} '{conflict_value}' already exists"
    return {
        "message": message or default_message,
        "error_code": "CONFLICT",
        "details": {
            "resource_type": resource_type,
            "conflict_type": "duplicate_value",
            "conflict_field": conflict_field,
            "conflict_value": conflict_value
        }
    }