"""Tests for the SolutionOutlineService.

This module contains unit tests for the SolutionOutlineService class.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.solution_outlines import SolutionOutlineService
from app.domain.models.solution_outlines import SolutionOutline, SolutionOutlineStatus
from app.api.schemas.solution_outlines import SolutionOutlineCreate
from app.core.exceptions import NotFoundException

class TestSolutionOutlineService:
    """Test cases for the SolutionOutlineService class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.solution_outline_repository = MagicMock()
        self.project_repository = MagicMock()
        
        # Create service with mocked dependencies
        self.service = SolutionOutlineService(self.db)
        self.service.solution_outline_repository = self.solution_outline_repository
        self.service.project_repository = self.project_repository
        
        # Mock project
        self.project_id = "test-project"
        self.project = MagicMock()
        self.project.id = self.project_id
        
        # Mock solution outline
        self.solution_outline = MagicMock(spec=SolutionOutline)
        self.solution_outline.id = 1
        self.solution_outline.project_id = self.project_id
        self.solution_outline.content = "Test content"
        self.solution_outline.version = 1
        self.solution_outline.status = SolutionOutlineStatus.draft
    
    def test_create_solution_outline(self):
        """Test creating a solution outline."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.solution_outline_repository.create_with_version.return_value = self.solution_outline
        
        # Act
        result = self.service.create_solution_outline(self.project_id, "Test content")
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.solution_outline_repository.create_with_version.assert_called_once()
        assert result == self.solution_outline
    
    def test_create_solution_outline_project_not_found(self):
        """Test creating a solution outline when the project is not found."""
        # Arrange
        self.project_repository.get_or_404.side_effect = NotFoundException("Project not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.create_solution_outline(self.project_id, "Test content")
    
    def test_update_solution_outline(self):
        """Test updating a solution outline."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.solution_outline_repository.create_with_version.return_value = self.solution_outline
        
        # Act
        result = self.service.update_solution_outline(self.project_id, "Updated content")
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.solution_outline_repository.create_with_version.assert_called_once()
        assert result == self.solution_outline
    
    def test_get_latest_solution_outline(self):
        """Test getting the latest solution outline."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.solution_outline_repository.get_latest_version.return_value = self.solution_outline
        
        # Act
        result = self.service.get_latest_solution_outline(self.project_id)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.solution_outline_repository.get_latest_version.assert_called_once_with(self.db, project_id=self.project_id)
        assert result == self.solution_outline
    
    def test_get_latest_solution_outline_not_found(self):
        """Test getting the latest solution outline when none exists."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.solution_outline_repository.get_latest_version.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.get_latest_solution_outline(self.project_id)
    
    def test_get_solution_outline_by_version(self):
        """Test getting a solution outline by version."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.solution_outline_repository.get_by_version_or_404.return_value = self.solution_outline
        
        # Act
        result = self.service.get_solution_outline_by_version(self.project_id, 1)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.solution_outline_repository.get_by_version_or_404.assert_called_once_with(
            self.db, project_id=self.project_id, version=1
        )
        assert result == self.solution_outline
    
    def test_get_solution_outline_versions(self):
        """Test getting all solution outline versions."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.solution_outline_repository.get_all_versions.return_value = [self.solution_outline]
        
        # Act
        result = self.service.get_solution_outline_versions(self.project_id)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.solution_outline_repository.get_all_versions.assert_called_once_with(
            self.db, project_id=self.project_id, skip=0, limit=100
        )
        assert result == [self.solution_outline]
    
    def test_update_solution_outline_status(self):
        """Test updating a solution outline status."""
        # Arrange
        self.solution_outline_repository.get_or_404.return_value = self.solution_outline
        self.solution_outline_repository.update_status.return_value = self.solution_outline
        
        # Act
        result = self.service.update_solution_outline_status(1, SolutionOutlineStatus.published)
        
        # Assert
        self.solution_outline_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.solution_outline_repository.update_status.assert_called_once_with(
            self.db, id=1, status=SolutionOutlineStatus.published
        )
        assert result == self.solution_outline
    
    def test_delete_solution_outline(self):
        """Test deleting a solution outline."""
        # Arrange
        self.solution_outline_repository.get_or_404.return_value = self.solution_outline
        self.solution_outline_repository.delete.return_value = self.solution_outline
        
        # Act
        result = self.service.delete_solution_outline(1)
        
        # Assert
        self.solution_outline_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.solution_outline_repository.delete.assert_called_once_with(self.db, id=1)
        assert result == self.solution_outline
    
    def test_get_solution_outline_with_review_comments(self):
        """Test getting a solution outline with review comments."""
        # Arrange
        self.solution_outline_repository.get_with_review_comments.return_value = self.solution_outline
        
        # Act
        result = self.service.get_solution_outline_with_review_comments(1)
        
        # Assert
        self.solution_outline_repository.get_with_review_comments.assert_called_once_with(self.db, id=1)
        assert result == self.solution_outline
    
    def test_get_solution_outline_with_review_comments_not_found(self):
        """Test getting a solution outline with review comments when it doesn't exist."""
        # Arrange
        self.solution_outline_repository.get_with_review_comments.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.get_solution_outline_with_review_comments(1)