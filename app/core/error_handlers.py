"""Error handling utilities.

This module provides utilities for handling errors in a consistent way across the application.
"""
import functools
import logging
from typing import Callable, TypeVar, Any, Dict, Optional
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import (
    AppException,
    DatabaseException,
    NotFoundException,
    BadRequestException,
)

logger = logging.getLogger(__name__)

# Type variables for generic functions
T = TypeVar('T')
F = TypeVar('F', bound=Callable[..., Any])

def handle_exceptions(func: F) -> F:
    """Decorator to handle exceptions in a consistent way.
    
    This decorator catches common exceptions and converts them to appropriate HTTP responses.
    
    Args:
        func: The function to decorate.
        
    Returns:
        The decorated function.
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AppException:
            # AppExceptions are already properly formatted, so just re-raise them
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in {func.__name__}: {e}", exc_info=True)
            raise DatabaseException(f"Database error: {str(e)}", original_exception=e)
        except HTTPException:
            # HTTPExceptions are already properly formatted, so just re-raise them
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}", exc_info=True)
            raise AppException(f"Internal server error: {str(e)}")
    return wrapper  # type: ignore

def handle_not_found(
    resource_type: str,
    resource_id: Optional[Any] = None,
    custom_message: Optional[str] = None
) -> None:
    """Raise a NotFoundException with appropriate details.
    
    Args:
        resource_type: The type of resource that was not found.
        resource_id: The ID of the resource that was not found.
        custom_message: A custom error message.
        
    Raises:
        NotFoundException: Always raised with the provided details.
    """
    message = custom_message or f"{resource_type} not found"
    if resource_id is not None:
        message = f"{message} with ID {resource_id}"
    raise NotFoundException(message, resource_type=resource_type, resource_id=resource_id)

def validate_entity_exists(entity: Optional[T], resource_type: str, resource_id: Any) -> T:
    """Validate that an entity exists and return it.
    
    Args:
        entity: The entity to validate.
        resource_type: The type of resource.
        resource_id: The ID of the resource.
        
    Returns:
        The entity if it exists.
        
    Raises:
        NotFoundException: If the entity does not exist.
    """
    if entity is None:
        handle_not_found(resource_type, resource_id)
    return entity  # type: ignore