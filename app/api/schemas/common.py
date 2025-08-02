"""Common API schemas for standardized responses."""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')

class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all API responses."""
    success: bool = Field(description="Indicates if the request was successful")
    message: str = Field(description="Human-readable message about the response")
    data: Optional[T] = Field(default=None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

class SuccessResponse(BaseResponse[T]):
    """Success response model."""
    success: bool = Field(default=True, description="Always true for success responses")

class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(default=False, description="Always false for error responses")
    message: str = Field(description="Error message")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class ValidationErrorResponse(ErrorResponse):
    """Validation error response model."""
    error_code: str = Field(default="VALIDATION_ERROR", description="Validation error code")
    details: Optional[List[Dict[str, Any]]] = Field(default=None, description="Validation error details")

class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items")
    pages: int = Field(ge=0, description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")

class PaginatedResponse(BaseResponse[List[T]]):
    """Paginated response model."""
    meta: PaginationMeta = Field(description="Pagination metadata")

class ListResponse(BaseResponse[List[T]]):
    """List response model for non-paginated lists."""
    count: int = Field(ge=0, description="Number of items in the response")

# Response utility functions
def create_success_response(
    data: Any = None,
    message: str = "Success",
) -> SuccessResponse:
    """Create a standardized success response."""
    return SuccessResponse(
        success=True,
        message=message,
        data=data,
        timestamp=datetime.utcnow()
    )

def create_error_response(
    message: str,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> ErrorResponse:
    """Create a standardized error response."""
    return ErrorResponse(
        success=False,
        message=message,
        error_code=error_code,
        details=details,
        timestamp=datetime.utcnow()
    )

def create_validation_error_response(
    message: str = "Validation failed",
    details: Optional[List[Dict[str, Any]]] = None,
) -> ValidationErrorResponse:
    """Create a standardized validation error response."""
    return ValidationErrorResponse(
        success=False,
        message=message,
        error_code="VALIDATION_ERROR",
        details=details,
        timestamp=datetime.utcnow()
    )

def create_list_response(
    data: List[Any],
    message: str = "Success",
) -> ListResponse:
    """Create a standardized list response."""
    return ListResponse(
        success=True,
        message=message,
        data=data,
        count=len(data),
        timestamp=datetime.utcnow()
    )

def create_paginated_response(
    data: List[Any],
    page: int,
    per_page: int,
    total: int,
    message: str = "Success",
) -> PaginatedResponse:
    """Create a standardized paginated response."""
    pages = (total + per_page - 1) // per_page  # Ceiling division
    has_next = page < pages
    has_prev = page > 1
    
    meta = PaginationMeta(
        page=page,
        per_page=per_page,
        total=total,
        pages=pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
    return PaginatedResponse(
        success=True,
        message=message,
        data=data,
        meta=meta,
        timestamp=datetime.utcnow()
    )