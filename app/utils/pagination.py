"""Pagination utilities."""
from typing import Any, Dict, List, Optional, Type, TypeVar, Generic
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Query
from sqlalchemy import asc, desc, func
from enum import Enum
from dataclasses import dataclass

T = TypeVar('T')

class SortOrder(str, Enum):
    """Sort order enum."""
    ASC = "asc"
    DESC = "desc"

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(default=1, ge=1, description="Page number (1-based)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(default=None, description="Field to sort by")
    sort_order: SortOrder = Field(default=SortOrder.ASC, description="Sort order")
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be >= 1')
        return v
    
    @validator('per_page')
    def validate_per_page(cls, v):
        if v < 1 or v > 100:
            raise ValueError('Per page must be between 1 and 100')
        return v

class FilterParams(BaseModel):
    """Base filter parameters."""
    search: Optional[str] = Field(default=None, description="Search term")

@dataclass
class PaginationResult(Generic[T]):
    """Pagination result for internal use (not a Pydantic model)."""
    items: List[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool


class PaginatedResponse(BaseModel, Generic[T]):
    """Pydantic model for paginated API responses."""
    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    per_page: int = Field(description="Items per page")
    pages: int = Field(description="Total number of pages")
    has_next: bool = Field(description="Whether there is a next page")
    has_prev: bool = Field(description="Whether there is a previous page")
    
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

class Paginator:
    """Utility class for handling pagination."""
    
    @staticmethod
    def paginate_query(
        query: Query,
        page: int,
        per_page: int,
        sort_by: Optional[str] = None,
        sort_order: SortOrder = SortOrder.ASC,
        allowed_sort_fields: Optional[List[str]] = None,
    ) -> PaginationResult:
        """
        Paginate a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query to paginate
            page: Page number (1-based)
            per_page: Items per page
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            allowed_sort_fields: List of allowed sort fields for security
            
        Returns:
            PaginationResult with paginated data
        """
        # Validate sort field
        if sort_by and allowed_sort_fields and sort_by not in allowed_sort_fields:
            raise ValueError(f"Invalid sort field: {sort_by}. Allowed fields: {allowed_sort_fields}")
        
        # Apply sorting if specified
        if sort_by:
            try:
                # Get the model from the query
                model = query.column_descriptions[0]['type']
                sort_column = getattr(model, sort_by)
                
                if sort_order == SortOrder.DESC:
                    query = query.order_by(desc(sort_column))
                else:
                    query = query.order_by(asc(sort_column))
            except AttributeError:
                # If sort field doesn't exist, ignore sorting
                pass
        
        # Get total count
        total = query.count()
        
        # Calculate pagination values
        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1
        
        # Apply pagination
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()
        
        return PaginationResult(
            items=items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    @staticmethod
    def paginate_list(
        items: List[T],
        page: int,
        per_page: int,
    ) -> PaginationResult[T]:
        """
        Paginate a list of items.
        
        Args:
            items: List of items to paginate
            page: Page number (1-based)
            per_page: Items per page
            
        Returns:
            PaginationResult with paginated data
        """
        total = len(items)
        pages = (total + per_page - 1) // per_page  # Ceiling division
        has_next = page < pages
        has_prev = page > 1
        
        # Calculate slice indices
        start = (page - 1) * per_page
        end = start + per_page
        
        # Get paginated items
        paginated_items = items[start:end]
        
        return PaginationResult(
            items=paginated_items,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )

def create_pagination_params(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> PaginationParams:
    """Create pagination parameters with validation."""
    return PaginationParams(
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=SortOrder(sort_order.lower())
    )

def get_pagination_params(
    page: int = 1,
    per_page: int = 20,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
) -> PaginationParams:
    """FastAPI dependency for pagination parameters."""
    return create_pagination_params(page, per_page, sort_by, sort_order)