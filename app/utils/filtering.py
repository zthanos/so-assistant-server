"""Filtering utilities for API endpoints."""
from typing import Any, Dict, List, Optional, Type, Union
from sqlalchemy.orm import Query
from sqlalchemy import and_, or_, func
from datetime import datetime
from enum import Enum

class FilterOperator(str, Enum):
    """Filter operators."""
    EQ = "eq"          # Equal
    NE = "ne"          # Not equal
    GT = "gt"          # Greater than
    GTE = "gte"        # Greater than or equal
    LT = "lt"          # Less than
    LTE = "lte"        # Less than or equal
    LIKE = "like"      # Like (case-sensitive)
    ILIKE = "ilike"    # Like (case-insensitive)
    IN = "in"          # In list
    NOT_IN = "not_in"  # Not in list
    IS_NULL = "is_null"        # Is null
    IS_NOT_NULL = "is_not_null"  # Is not null

class FilterCondition:
    """Represents a single filter condition."""
    
    def __init__(
        self,
        field: str,
        operator: FilterOperator,
        value: Any = None,
        case_sensitive: bool = True
    ):
        self.field = field
        self.operator = operator
        self.value = value
        self.case_sensitive = case_sensitive

class QueryFilter:
    """Utility class for applying filters to SQLAlchemy queries."""
    
    @staticmethod
    def apply_filters(
        query: Query,
        filters: List[FilterCondition],
        model: Type,
        allowed_fields: Optional[List[str]] = None,
    ) -> Query:
        """
        Apply filters to a SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query to filter
            filters: List of filter conditions
            model: SQLAlchemy model class
            allowed_fields: List of allowed filter fields for security
            
        Returns:
            Filtered query
        """
        for filter_condition in filters:
            # Validate field if allowed_fields is specified
            if allowed_fields and filter_condition.field not in allowed_fields:
                continue  # Skip invalid fields
            
            try:
                # Get the column from the model
                column = getattr(model, filter_condition.field)
                
                # Apply the filter based on operator
                condition = QueryFilter._build_condition(
                    column, filter_condition.operator, filter_condition.value
                )
                
                if condition is not None:
                    query = query.filter(condition)
                    
            except AttributeError:
                # Field doesn't exist on model, skip
                continue
        
        return query
    
    @staticmethod
    def _build_condition(column, operator: FilterOperator, value: Any):
        """Build a SQLAlchemy condition based on operator and value."""
        if operator == FilterOperator.EQ:
            return column == value
        elif operator == FilterOperator.NE:
            return column != value
        elif operator == FilterOperator.GT:
            return column > value
        elif operator == FilterOperator.GTE:
            return column >= value
        elif operator == FilterOperator.LT:
            return column < value
        elif operator == FilterOperator.LTE:
            return column <= value
        elif operator == FilterOperator.LIKE:
            return column.like(f"%{value}%")
        elif operator == FilterOperator.ILIKE:
            return column.ilike(f"%{value}%")
        elif operator == FilterOperator.IN:
            if isinstance(value, (list, tuple)):
                return column.in_(value)
        elif operator == FilterOperator.NOT_IN:
            if isinstance(value, (list, tuple)):
                return ~column.in_(value)
        elif operator == FilterOperator.IS_NULL:
            return column.is_(None)
        elif operator == FilterOperator.IS_NOT_NULL:
            return column.isnot(None)
        
        return None
    
    @staticmethod
    def apply_search(
        query: Query,
        search_term: str,
        search_fields: List[str],
        model: Type,
        case_sensitive: bool = False,
    ) -> Query:
        """
        Apply search across multiple fields.
        
        Args:
            query: SQLAlchemy query to filter
            search_term: Search term
            search_fields: List of fields to search in
            model: SQLAlchemy model class
            case_sensitive: Whether search should be case-sensitive
            
        Returns:
            Filtered query with search conditions
        """
        if not search_term or not search_fields:
            return query
        
        search_conditions = []
        
        for field in search_fields:
            try:
                column = getattr(model, field)
                if case_sensitive:
                    condition = column.like(f"%{search_term}%")
                else:
                    condition = column.ilike(f"%{search_term}%")
                search_conditions.append(condition)
            except AttributeError:
                # Field doesn't exist, skip
                continue
        
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        
        return query

def parse_filter_params(filter_params: Dict[str, Any]) -> List[FilterCondition]:
    """
    Parse filter parameters from request into FilterCondition objects.
    
    Expected format:
    - Simple filters: {"field": "value"}
    - Complex filters: {"field__operator": "value"}
    
    Examples:
    - {"name": "John"} -> FilterCondition("name", FilterOperator.EQ, "John")
    - {"age__gte": 18} -> FilterCondition("age", FilterOperator.GTE, 18)
    - {"status__in": ["active", "pending"]} -> FilterCondition("status", FilterOperator.IN, ["active", "pending"])
    """
    filters = []
    
    for key, value in filter_params.items():
        if value is None:
            continue
        
        # Parse field and operator
        if "__" in key:
            field, operator_str = key.split("__", 1)
            try:
                operator = FilterOperator(operator_str)
            except ValueError:
                # Invalid operator, treat as simple equality
                field = key
                operator = FilterOperator.EQ
        else:
            field = key
            operator = FilterOperator.EQ
        
        filters.append(FilterCondition(field, operator, value))
    
    return filters

def create_date_range_filters(
    field: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[FilterCondition]:
    """Create date range filters for a field."""
    filters = []
    
    if start_date:
        filters.append(FilterCondition(field, FilterOperator.GTE, start_date))
    
    if end_date:
        filters.append(FilterCondition(field, FilterOperator.LTE, end_date))
    
    return filters