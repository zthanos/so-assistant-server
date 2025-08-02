"""Tests for pagination utilities.

This module contains unit tests for the pagination utilities.
"""
import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Query
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base

from app.utils.pagination import (
    PaginationParams, 
    PaginationResult, 
    Paginator, 
    SortOrder,
    create_pagination_params,
    get_pagination_params
)

# Create test model
Base = declarative_base()

class TestModel(Base):
    """Test SQLAlchemy model."""
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))

class TestPaginationParams:
    """Test cases for PaginationParams."""
    
    def test_default_values(self):
        """Test default pagination parameters."""
        params = PaginationParams()
        
        assert params.page == 1
        assert params.per_page == 20
        assert params.sort_by is None
        assert params.sort_order == SortOrder.ASC

    def test_custom_values(self):
        """Test custom pagination parameters."""
        params = PaginationParams(
            page=2,
            per_page=50,
            sort_by="name",
            sort_order=SortOrder.DESC
        )
        
        assert params.page == 2
        assert params.per_page == 50
        assert params.sort_by == "name"
        assert params.sort_order == SortOrder.DESC

    def test_page_validation(self):
        """Test page validation."""
        with pytest.raises(ValueError):
            PaginationParams(page=0)
        
        with pytest.raises(ValueError):
            PaginationParams(page=-1)

    def test_per_page_validation(self):
        """Test per_page validation."""
        with pytest.raises(ValueError):
            PaginationParams(per_page=0)
        
        with pytest.raises(ValueError):
            PaginationParams(per_page=101)

class TestPaginationResult:
    """Test cases for PaginationResult."""
    
    def test_pagination_result_creation(self):
        """Test creating a pagination result."""
        items = [1, 2, 3, 4, 5]
        result = PaginationResult(
            items=items,
            total=100,
            page=2,
            per_page=20,
            pages=5,
            has_next=True,
            has_prev=True
        )
        
        assert result.items == items
        assert result.total == 100
        assert result.page == 2
        assert result.per_page == 20
        assert result.pages == 5
        assert result.has_next is True
        assert result.has_prev is True

class TestPaginator:
    """Test cases for Paginator."""
    
    def test_paginate_list_first_page(self):
        """Test paginating a list - first page."""
        items = list(range(1, 101))  # 100 items
        
        result = Paginator.paginate_list(items, page=1, per_page=20)
        
        assert len(result.items) == 20
        assert result.items == list(range(1, 21))
        assert result.total == 100
        assert result.page == 1
        assert result.per_page == 20
        assert result.pages == 5
        assert result.has_next is True
        assert result.has_prev is False

    def test_paginate_list_middle_page(self):
        """Test paginating a list - middle page."""
        items = list(range(1, 101))  # 100 items
        
        result = Paginator.paginate_list(items, page=3, per_page=20)
        
        assert len(result.items) == 20
        assert result.items == list(range(41, 61))
        assert result.total == 100
        assert result.page == 3
        assert result.per_page == 20
        assert result.pages == 5
        assert result.has_next is True
        assert result.has_prev is True

    def test_paginate_list_last_page(self):
        """Test paginating a list - last page."""
        items = list(range(1, 101))  # 100 items
        
        result = Paginator.paginate_list(items, page=5, per_page=20)
        
        assert len(result.items) == 20
        assert result.items == list(range(81, 101))
        assert result.total == 100
        assert result.page == 5
        assert result.per_page == 20
        assert result.pages == 5
        assert result.has_next is False
        assert result.has_prev is True

    def test_paginate_list_partial_last_page(self):
        """Test paginating a list - partial last page."""
        items = list(range(1, 96))  # 95 items
        
        result = Paginator.paginate_list(items, page=5, per_page=20)
        
        assert len(result.items) == 15
        assert result.items == list(range(81, 96))
        assert result.total == 95
        assert result.page == 5
        assert result.per_page == 20
        assert result.pages == 5
        assert result.has_next is False
        assert result.has_prev is True

    def test_paginate_list_empty(self):
        """Test paginating an empty list."""
        items = []
        
        result = Paginator.paginate_list(items, page=1, per_page=20)
        
        assert len(result.items) == 0
        assert result.items == []
        assert result.total == 0
        assert result.page == 1
        assert result.per_page == 20
        assert result.pages == 0
        assert result.has_next is False
        assert result.has_prev is False

    def test_paginate_query_basic(self):
        """Test paginating a query - basic functionality."""
        # Arrange
        mock_query = MagicMock(spec=Query)
        mock_query.count.return_value = 100
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = list(range(1, 21))
        
        # Mock column descriptions for model detection
        mock_query.column_descriptions = [{'type': TestModel}]
        
        # Act
        result = Paginator.paginate_query(
            mock_query,
            page=1,
            per_page=20
        )
        
        # Assert
        assert len(result.items) == 20
        assert result.total == 100
        assert result.page == 1
        assert result.per_page == 20
        assert result.pages == 5
        assert result.has_next is True
        assert result.has_prev is False
        
        mock_query.count.assert_called_once()
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(20)
        mock_query.all.assert_called_once()

    def test_paginate_query_with_sorting(self):
        """Test paginating a query with sorting."""
        # Arrange
        mock_query = MagicMock(spec=Query)
        mock_query.count.return_value = 100
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = list(range(1, 21))
        
        # Mock column descriptions for model detection
        mock_query.column_descriptions = [{'type': TestModel}]
        
        # Act
        result = Paginator.paginate_query(
            mock_query,
            page=1,
            per_page=20,
            sort_by="name",
            sort_order=SortOrder.ASC,
            allowed_sort_fields=["name", "id"]
        )
        
        # Assert
        assert result.total == 100
        mock_query.order_by.assert_called_once()

    def test_paginate_query_invalid_sort_field(self):
        """Test paginating a query with invalid sort field."""
        # Arrange
        mock_query = MagicMock(spec=Query)
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid sort field"):
            Paginator.paginate_query(
                mock_query,
                page=1,
                per_page=20,
                sort_by="invalid_field",
                allowed_sort_fields=["name", "id"]
            )

class TestPaginationHelpers:
    """Test cases for pagination helper functions."""
    
    def test_create_pagination_params(self):
        """Test creating pagination parameters."""
        params = create_pagination_params(
            page=2,
            per_page=50,
            sort_by="name",
            sort_order="desc"
        )
        
        assert params.page == 2
        assert params.per_page == 50
        assert params.sort_by == "name"
        assert params.sort_order == SortOrder.DESC

    def test_get_pagination_params(self):
        """Test getting pagination parameters (FastAPI dependency)."""
        params = get_pagination_params(
            page=3,
            per_page=25,
            sort_by="created_at",
            sort_order="asc"
        )
        
        assert params.page == 3
        assert params.per_page == 25
        assert params.sort_by == "created_at"
        assert params.sort_order == SortOrder.ASC