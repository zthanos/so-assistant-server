"""Tests for filtering utilities.

This module contains unit tests for the filtering utilities.
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Query
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from app.utils.filtering import (
    FilterOperator,
    FilterCondition,
    QueryFilter,
    parse_filter_params,
    create_date_range_filters
)
from datetime import datetime

# Create test model
Base = declarative_base()

class TestModel(Base):
    """Test SQLAlchemy model."""
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    created_at = Column(String(255))  # Simplified for testing

class TestFilterOperator:
    """Test cases for FilterOperator enum."""
    
    def test_filter_operators(self):
        """Test filter operator values."""
        assert FilterOperator.EQ == "eq"
        assert FilterOperator.NE == "ne"
        assert FilterOperator.GT == "gt"
        assert FilterOperator.GTE == "gte"
        assert FilterOperator.LT == "lt"
        assert FilterOperator.LTE == "lte"
        assert FilterOperator.LIKE == "like"
        assert FilterOperator.ILIKE == "ilike"
        assert FilterOperator.IN == "in"
        assert FilterOperator.NOT_IN == "not_in"
        assert FilterOperator.IS_NULL == "is_null"
        assert FilterOperator.IS_NOT_NULL == "is_not_null"

class TestFilterCondition:
    """Test cases for FilterCondition."""
    
    def test_filter_condition_creation(self):
        """Test creating a filter condition."""
        condition = FilterCondition(
            field="name",
            operator=FilterOperator.EQ,
            value="test",
            case_sensitive=True
        )
        
        assert condition.field == "name"
        assert condition.operator == FilterOperator.EQ
        assert condition.value == "test"
        assert condition.case_sensitive is True

    def test_filter_condition_defaults(self):
        """Test filter condition default values."""
        condition = FilterCondition(
            field="name",
            operator=FilterOperator.LIKE,
            value="test"
        )
        
        assert condition.case_sensitive is True

class TestQueryFilter:
    """Test cases for QueryFilter."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_query = MagicMock(spec=Query)
        self.mock_column = MagicMock()
        
        # Mock getattr to return our mock column
        self.original_getattr = getattr
        
    def test_apply_filters_eq(self):
        """Test applying EQ filter."""
        # Arrange
        filters = [FilterCondition("name", FilterOperator.EQ, "test")]
        
        with pytest.mock.patch('builtins.getattr', return_value=self.mock_column):
            # Act
            result = QueryFilter.apply_filters(
                self.mock_query, 
                filters, 
                TestModel, 
                allowed_fields=["name"]
            )
            
            # Assert
            self.mock_query.filter.assert_called_once()

    def test_apply_filters_invalid_field(self):
        """Test applying filter with invalid field."""
        # Arrange
        filters = [FilterCondition("invalid_field", FilterOperator.EQ, "test")]
        
        # Act
        result = QueryFilter.apply_filters(
            self.mock_query, 
            filters, 
            TestModel, 
            allowed_fields=["name"]
        )
        
        # Assert - should not call filter since field is not allowed
        assert result == self.mock_query

    def test_apply_filters_no_allowed_fields(self):
        """Test applying filters without allowed fields restriction."""
        # Arrange
        filters = [FilterCondition("name", FilterOperator.EQ, "test")]
        
        with pytest.mock.patch('builtins.getattr', return_value=self.mock_column):
            # Act
            result = QueryFilter.apply_filters(
                self.mock_query, 
                filters, 
                TestModel
            )
            
            # Assert
            self.mock_query.filter.assert_called_once()

    def test_apply_search(self):
        """Test applying search filter."""
        # Arrange
        search_term = "test"
        search_fields = ["name", "description"]
        
        with pytest.mock.patch('builtins.getattr', return_value=self.mock_column):
            # Act
            result = QueryFilter.apply_search(
                self.mock_query,
                search_term,
                search_fields,
                TestModel
            )
            
            # Assert
            self.mock_query.filter.assert_called_once()

    def test_apply_search_empty_term(self):
        """Test applying search with empty term."""
        # Arrange
        search_term = ""
        search_fields = ["name", "description"]
        
        # Act
        result = QueryFilter.apply_search(
            self.mock_query,
            search_term,
            search_fields,
            TestModel
        )
        
        # Assert - should return original query without filtering
        assert result == self.mock_query
        self.mock_query.filter.assert_not_called()

    def test_apply_search_no_fields(self):
        """Test applying search with no fields."""
        # Arrange
        search_term = "test"
        search_fields = []
        
        # Act
        result = QueryFilter.apply_search(
            self.mock_query,
            search_term,
            search_fields,
            TestModel
        )
        
        # Assert - should return original query without filtering
        assert result == self.mock_query
        self.mock_query.filter.assert_not_called()

    def test_build_condition_eq(self):
        """Test building EQ condition."""
        condition = QueryFilter._build_condition(
            self.mock_column, 
            FilterOperator.EQ, 
            "test"
        )
        
        assert condition is not None

    def test_build_condition_in(self):
        """Test building IN condition."""
        condition = QueryFilter._build_condition(
            self.mock_column, 
            FilterOperator.IN, 
            ["value1", "value2"]
        )
        
        assert condition is not None

    def test_build_condition_in_invalid_value(self):
        """Test building IN condition with invalid value."""
        condition = QueryFilter._build_condition(
            self.mock_column, 
            FilterOperator.IN, 
            "not_a_list"
        )
        
        assert condition is None

    def test_build_condition_is_null(self):
        """Test building IS_NULL condition."""
        condition = QueryFilter._build_condition(
            self.mock_column, 
            FilterOperator.IS_NULL, 
            None
        )
        
        assert condition is not None

class TestParseFilterParams:
    """Test cases for parse_filter_params function."""
    
    def test_parse_simple_filters(self):
        """Test parsing simple filter parameters."""
        filter_params = {
            "name": "John",
            "age": "25"
        }
        
        filters = parse_filter_params(filter_params)
        
        assert len(filters) == 2
        assert filters[0].field == "name"
        assert filters[0].operator == FilterOperator.EQ
        assert filters[0].value == "John"
        
        assert filters[1].field == "age"
        assert filters[1].operator == FilterOperator.EQ
        assert filters[1].value == "25"

    def test_parse_complex_filters(self):
        """Test parsing complex filter parameters."""
        filter_params = {
            "age__gte": "18",
            "name__like": "John",
            "status__in": "active,pending"
        }
        
        filters = parse_filter_params(filter_params)
        
        assert len(filters) == 3
        
        # Check age filter
        age_filter = next(f for f in filters if f.field == "age")
        assert age_filter.operator == FilterOperator.GTE
        assert age_filter.value == "18"
        
        # Check name filter
        name_filter = next(f for f in filters if f.field == "name")
        assert name_filter.operator == FilterOperator.LIKE
        assert name_filter.value == "John"
        
        # Check status filter
        status_filter = next(f for f in filters if f.field == "status")
        assert status_filter.operator == FilterOperator.IN
        assert status_filter.value == ["active", "pending"]

    def test_parse_filters_with_none_values(self):
        """Test parsing filter parameters with None values."""
        filter_params = {
            "name": "John",
            "age": None,
            "status": ""
        }
        
        filters = parse_filter_params(filter_params)
        
        # Should only include non-None values
        assert len(filters) == 1
        assert filters[0].field == "name"
        assert filters[0].value == "John"

    def test_parse_filters_invalid_operator(self):
        """Test parsing filter parameters with invalid operator."""
        filter_params = {
            "name__invalid": "John"
        }
        
        filters = parse_filter_params(filter_params)
        
        # Should treat as simple equality
        assert len(filters) == 1
        assert filters[0].field == "name__invalid"
        assert filters[0].operator == FilterOperator.EQ
        assert filters[0].value == "John"

class TestCreateDateRangeFilters:
    """Test cases for create_date_range_filters function."""
    
    def test_create_date_range_both_dates(self):
        """Test creating date range filters with both start and end dates."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 12, 31)
        
        filters = create_date_range_filters("created_at", start_date, end_date)
        
        assert len(filters) == 2
        
        start_filter = filters[0]
        assert start_filter.field == "created_at"
        assert start_filter.operator == FilterOperator.GTE
        assert start_filter.value == start_date
        
        end_filter = filters[1]
        assert end_filter.field == "created_at"
        assert end_filter.operator == FilterOperator.LTE
        assert end_filter.value == end_date

    def test_create_date_range_start_only(self):
        """Test creating date range filters with start date only."""
        start_date = datetime(2023, 1, 1)
        
        filters = create_date_range_filters("created_at", start_date=start_date)
        
        assert len(filters) == 1
        assert filters[0].field == "created_at"
        assert filters[0].operator == FilterOperator.GTE
        assert filters[0].value == start_date

    def test_create_date_range_end_only(self):
        """Test creating date range filters with end date only."""
        end_date = datetime(2023, 12, 31)
        
        filters = create_date_range_filters("created_at", end_date=end_date)
        
        assert len(filters) == 1
        assert filters[0].field == "created_at"
        assert filters[0].operator == FilterOperator.LTE
        assert filters[0].value == end_date

    def test_create_date_range_no_dates(self):
        """Test creating date range filters with no dates."""
        filters = create_date_range_filters("created_at")
        
        assert len(filters) == 0