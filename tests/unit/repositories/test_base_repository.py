"""Tests for the BaseRepository.

This module contains unit tests for the BaseRepository class.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

from app.repositories.base import BaseRepository
from app.core.exceptions import NotFoundException

# Create test models
Base = declarative_base()

class TestModel(Base):
    """Test SQLAlchemy model."""
    __tablename__ = "test_models"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))

class TestCreateSchema(BaseModel):
    """Test create schema."""
    name: str
    description: str = None

class TestUpdateSchema(BaseModel):
    """Test update schema."""
    name: str = None
    description: str = None

class TestRepository(BaseRepository[TestModel, TestCreateSchema, TestUpdateSchema]):
    """Test repository implementation."""
    pass

class TestBaseRepository:
    """Test cases for the BaseRepository class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.repository = TestRepository(TestModel)
        
        # Mock model instance
        self.model_instance = MagicMock(spec=TestModel)
        self.model_instance.id = 1
        self.model_instance.name = "Test Item"
        self.model_instance.description = "Test Description"

    def test_get_existing_item(self):
        """Test getting an existing item by ID."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = self.model_instance
        
        # Act
        result = self.repository.get(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        assert result == self.model_instance

    def test_get_non_existing_item(self):
        """Test getting a non-existing item by ID."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.repository.get(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        assert result is None

    def test_get_or_404_existing_item(self):
        """Test getting an existing item by ID with 404 handling."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = self.model_instance
        
        # Act
        result = self.repository.get_or_404(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        assert result == self.model_instance

    def test_get_or_404_non_existing_item(self):
        """Test getting a non-existing item by ID with 404 handling."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.repository.get_or_404(self.db, id=1)

    def test_get_multi(self):
        """Test getting multiple items."""
        # Arrange
        items = [self.model_instance, MagicMock(spec=TestModel)]
        self.db.query.return_value.offset.return_value.limit.return_value.all.return_value = items
        
        # Act
        result = self.repository.get_multi(self.db, skip=0, limit=10)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        self.db.query.return_value.offset.assert_called_once_with(0)
        self.db.query.return_value.offset.return_value.limit.assert_called_once_with(10)
        assert result == items

    def test_create(self):
        """Test creating a new item."""
        # Arrange
        create_data = TestCreateSchema(name="New Item", description="New Description")
        
        with patch.object(TestModel, '__init__', return_value=None) as mock_init:
            mock_instance = MagicMock(spec=TestModel)
            
            with patch.object(TestModel, '__new__', return_value=mock_instance):
                # Act
                result = self.repository.create(self.db, obj_in=create_data)
                
                # Assert
                self.db.add.assert_called_once_with(mock_instance)
                self.db.commit.assert_called_once()
                self.db.refresh.assert_called_once_with(mock_instance)
                assert result == mock_instance

    def test_update(self):
        """Test updating an existing item."""
        # Arrange
        update_data = TestUpdateSchema(name="Updated Item")
        
        # Act
        result = self.repository.update(self.db, db_obj=self.model_instance, obj_in=update_data)
        
        # Assert
        assert self.model_instance.name == "Updated Item"
        self.db.add.assert_called_once_with(self.model_instance)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(self.model_instance)
        assert result == self.model_instance

    def test_update_with_dict(self):
        """Test updating an existing item with dictionary data."""
        # Arrange
        update_data = {"name": "Updated Item", "description": "Updated Description"}
        
        # Act
        result = self.repository.update(self.db, db_obj=self.model_instance, obj_in=update_data)
        
        # Assert
        assert self.model_instance.name == "Updated Item"
        assert self.model_instance.description == "Updated Description"
        self.db.add.assert_called_once_with(self.model_instance)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(self.model_instance)
        assert result == self.model_instance

    def test_delete(self):
        """Test deleting an item."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = self.model_instance
        
        # Act
        result = self.repository.delete(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        self.db.delete.assert_called_once_with(self.model_instance)
        self.db.commit.assert_called_once()
        assert result == self.model_instance

    def test_delete_non_existing_item(self):
        """Test deleting a non-existing item."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.repository.delete(self.db, id=1)

    def test_count(self):
        """Test counting items."""
        # Arrange
        self.db.query.return_value.count.return_value = 5
        
        # Act
        result = self.repository.count(self.db)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        self.db.query.return_value.count.assert_called_once()
        assert result == 5

    def test_exists(self):
        """Test checking if an item exists."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = self.model_instance
        
        # Act
        result = self.repository.exists(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        assert result is True

    def test_exists_non_existing_item(self):
        """Test checking if a non-existing item exists."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.repository.exists(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(TestModel)
        assert result is False