"""Tests for the Solution Outline API endpoints.

This module contains unit tests for the Solution Outline API endpoints.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.endpoints.solution_outlines import router
from app.domain.models.solution_outlines import SolutionOutlineStatus
from app.core.exceptions import NotFoundException

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Mock service
mock_service = MagicMock()

# Mock solution outline
mock_solution_outline = {
    "id": 1,
    "project_id": "test-project",
    "content": "Test content",
    "version": 1,
    "status": SolutionOutlineStatus.draft,
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

# Override dependencies
@pytest.fixture(autouse=True)
def override_dependencies():
    """Override dependencies for testing."""
    with patch("app.api.v1.endpoints.solution_outlines.get_solution_outline_service", return_value=mock_service):
        yield

class TestSolutionOutlineEndpoints:
    """Test cases for the Solution Outline API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset mock
        mock_service.reset_mock()
    
    def test_create_solution_outline(self):
        """Test creating a solution outline."""
        # Arrange
        mock_service.create_solution_outline.return_value = mock_solution_outline
        
        # Act
        response = client.post(
            "/projects/test-project/solution-outlines?content=Test%20content&status=draft"
        )
        
        # Assert
        assert response.status_code == 201
        mock_service.create_solution_outline.assert_called_once_with(
            "test-project", "Test content", SolutionOutlineStatus.draft
        )
        assert response.json() == mock_solution_outline
    
    def test_create_solution_outline_project_not_found(self):
        """Test creating a solution outline when the project is not found."""
        # Arrange
        mock_service.create_solution_outline.side_effect = NotFoundException("Project not found")
        
        # Act
        response = client.post(
            "/projects/test-project/solution-outlines?content=Test%20content&status=draft"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"
    
    def test_update_solution_outline(self):
        """Test updating a solution outline."""
        # Arrange
        mock_service.update_solution_outline.return_value = mock_solution_outline
        
        # Act
        response = client.put(
            "/projects/test-project/solution-outlines?content=Test%20content"
        )
        
        # Assert
        assert response.status_code == 200
        mock_service.update_solution_outline.assert_called_once_with(
            "test-project", "Test content", None
        )
        assert response.json() == mock_solution_outline
    
    def test_get_latest_solution_outline(self):
        """Test getting the latest solution outline."""
        # Arrange
        mock_service.get_latest_solution_outline.return_value = mock_solution_outline
        
        # Act
        response = client.get("/projects/test-project/solution-outlines/latest")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_latest_solution_outline.assert_called_once_with("test-project")
        assert response.json() == mock_solution_outline
    
    def test_get_solution_outline_by_version(self):
        """Test getting a solution outline by version."""
        # Arrange
        mock_service.get_solution_outline_by_version.return_value = mock_solution_outline
        
        # Act
        response = client.get("/projects/test-project/solution-outlines/1")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_solution_outline_by_version.assert_called_once_with("test-project", 1)
        assert response.json() == mock_solution_outline
    
    def test_get_solution_outline_versions(self):
        """Test getting all solution outline versions."""
        # Arrange
        mock_service.get_solution_outline_versions.return_value = [mock_solution_outline]
        
        # Act
        response = client.get("/projects/test-project/solution-outlines")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_solution_outline_versions.assert_called_once_with("test-project", 0, 100)
        assert response.json() == [mock_solution_outline]
    
    def test_update_solution_outline_status(self):
        """Test updating a solution outline status."""
        # Arrange
        mock_service.update_solution_outline_status.return_value = mock_solution_outline
        
        # Act
        response = client.patch("/solution-outlines/1/status?status=published")
        
        # Assert
        assert response.status_code == 200
        mock_service.update_solution_outline_status.assert_called_once_with(1, SolutionOutlineStatus.published)
        assert response.json() == mock_solution_outline
    
    def test_delete_solution_outline(self):
        """Test deleting a solution outline."""
        # Arrange
        mock_service.delete_solution_outline.return_value = mock_solution_outline
        
        # Act
        response = client.delete("/solution-outlines/1")
        
        # Assert
        assert response.status_code == 200
        mock_service.delete_solution_outline.assert_called_once_with(1)
        assert response.json() == mock_solution_outline
    
    def test_get_solution_outline_with_review_comments(self):
        """Test getting a solution outline with review comments."""
        # Arrange
        mock_service.get_solution_outline_with_review_comments.return_value = mock_solution_outline
        
        # Act
        response = client.get("/solution-outlines/1/with-comments")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_solution_outline_with_review_comments.assert_called_once_with(1)
        assert response.json() == mock_solution_outline