"""Tests for the ADRService.

This module contains unit tests for the ADRService class.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.adrs import ADRService
from app.domain.models.adrs import ADR
from app.api.schemas.adrs import ADRCreate, ADRUpdate
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

class TestADRService:
    """Test cases for the ADRService class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.adr_repository = MagicMock()
        self.project_repository = MagicMock()
        
        # Create service with mocked dependencies
        self.service = ADRService(self.db)
        self.service.adr_repository = self.adr_repository
        self.service.project_repository = self.project_repository
        
        # Mock project
        self.project_id = "test-project"
        self.project = MagicMock()
        self.project.id = self.project_id
        
        # Mock ADR
        self.adr = MagicMock(spec=ADR)
        self.adr.id = 1
        self.adr.project_id = self.project_id
        self.adr.title = "Test ADR"
        self.adr.content = "Test content"
    
    def test_create_adr(self):
        """Test creating an ADR."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.adr_repository.get_by_title.return_value = None
        self.adr_repository.create.return_value = self.adr
        
        # Act
        result = self.service.create_adr(self.project_id, "Test ADR", "Test content")
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.adr_repository.get_by_title.assert_called_once_with(
            self.db, project_id=self.project_id, title="Test ADR"
        )
        self.adr_repository.create.assert_called_once()
        assert result == self.adr
    
    def test_create_adr_project_not_found(self):
        """Test creating an ADR when the project is not found."""
        # Arrange
        self.project_repository.get_or_404.side_effect = NotFoundException("Project not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.create_adr(self.project_id, "Test ADR", "Test content")
    
    def test_create_adr_title_conflict(self):
        """Test creating an ADR with a title that already exists."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.adr_repository.get_by_title.return_value = self.adr
        
        # Act & Assert
        with pytest.raises(ConflictException):
            self.service.create_adr(self.project_id, "Test ADR", "Test content")
    
    def test_get_adr(self):
        """Test getting an ADR by ID."""
        # Arrange
        self.adr_repository.get_or_404.return_value = self.adr
        
        # Act
        result = self.service.get_adr(1)
        
        # Assert
        self.adr_repository.get_or_404.assert_called_once_with(self.db, 1)
        assert result == self.adr
    
    def test_get_adrs_for_project(self):
        """Test getting all ADRs for a project."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.adr_repository.get_by_project.return_value = [self.adr]
        
        # Act
        result = self.service.get_adrs_for_project(self.project_id)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.adr_repository.get_by_project.assert_called_once_with(
            self.db, project_id=self.project_id, skip=0, limit=100
        )
        assert result == [self.adr]
    
    def test_update_adr(self):
        """Test updating an ADR."""
        # Arrange
        self.adr_repository.get_or_404.return_value = self.adr
        self.adr_repository.get_by_title.return_value = None
        self.adr_repository.update.return_value = self.adr
        
        # Act
        result = self.service.update_adr(1, "Updated ADR", "Updated content")
        
        # Assert
        self.adr_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.adr_repository.get_by_title.assert_called_once_with(
            self.db, project_id=self.project_id, title="Updated ADR"
        )
        self.adr_repository.update.assert_called_once()
        assert result == self.adr
    
    def test_update_adr_no_fields(self):
        """Test updating an ADR with no fields provided."""
        # Arrange
        self.adr_repository.get_or_404.return_value = self.adr
        
        # Act & Assert
        with pytest.raises(BadRequestException):
            self.service.update_adr(1)
    
    def test_update_adr_title_conflict(self):
        """Test updating an ADR with a title that already exists."""
        # Arrange
        self.adr_repository.get_or_404.return_value = self.adr
        
        conflicting_adr = MagicMock(spec=ADR)
        conflicting_adr.id = 2
        
        self.adr_repository.get_by_title.return_value = conflicting_adr
        
        # Act & Assert
        with pytest.raises(ConflictException):
            self.service.update_adr(1, "Updated ADR", "Updated content")
    
    def test_delete_adr(self):
        """Test deleting an ADR."""
        # Arrange
        self.adr_repository.get_or_404.return_value = self.adr
        self.adr_repository.delete.return_value = self.adr
        
        # Act
        result = self.service.delete_adr(1)
        
        # Assert
        self.adr_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.adr_repository.delete.assert_called_once_with(self.db, id=1)
        assert result == self.adr
    
    def test_search_adrs(self):
        """Test searching ADRs."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.adr_repository.search_adrs.return_value = [self.adr]
        
        # Act
        result = self.service.search_adrs(self.project_id, "test")
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.adr_repository.search_adrs.assert_called_once_with(
            self.db, project_id=self.project_id, query="test", skip=0, limit=100
        )
        assert result == [self.adr]
    
    def test_get_recent_adrs(self):
        """Test getting recent ADRs."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.adr_repository.get_recent_adrs.return_value = [self.adr]
        
        # Act
        result = self.service.get_recent_adrs(self.project_id)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.adr_repository.get_recent_adrs.assert_called_once_with(
            self.db, project_id=self.project_id, limit=5
        )
        assert result == [self.adr]
    
    def test_count_adrs_for_project(self):
        """Test counting ADRs for a project."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.adr_repository.count_by_project.return_value = 1
        
        # Act
        result = self.service.count_adrs_for_project(self.project_id)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.adr_repository.count_by_project.assert_called_once_with(
            self.db, project_id=self.project_id
        )
        assert result == 1