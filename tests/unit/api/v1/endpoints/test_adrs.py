"""Tests for the ADR API endpoints.

This module contains unit tests for the Architecture Decision Record (ADR) API endpoints.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.endpoints.adrs import router
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Mock service
mock_service = MagicMock()

# Mock ADR
mock_adr = {
    "id": 1,
    "project_id": "test-project",
    "title": "Test ADR",
    "content": "Test content",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

# Override dependencies
@pytest.fixture(autouse=True)
def override_dependencies():
    """Override dependencies for testing."""
    with patch("app.api.v1.endpoints.adrs.get_adr_service", return_value=mock_service):
        yield

class TestADREndpoints:
    """Test cases for the ADR API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset mock
        mock_service.reset_mock()
    
    def test_create_adr(self):
        """Test creating an ADR."""
        # Arrange
        mock_service.create_adr.return_value = mock_adr
        
        # Act
        response = client.post(
            "/projects/test-project/adrs?title=Test%20ADR&content=Test%20content"
        )
        
        # Assert
        assert response.status_code == 201
        mock_service.create_adr.assert_called_once_with(
            "test-project", "Test ADR", "Test content"
        )
        assert response.json() == mock_adr
    
    def test_create_adr_project_not_found(self):
        """Test creating an ADR when the project is not found."""
        # Arrange
        mock_service.create_adr.side_effect = NotFoundException("Project not found")
        
        # Act
        response = client.post(
            "/projects/test-project/adrs?title=Test%20ADR&content=Test%20content"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Project not found"
    
    def test_create_adr_title_conflict(self):
        """Test creating an ADR with a title that already exists."""
        # Arrange
        mock_service.create_adr.side_effect = ConflictException("ADR with title 'Test ADR' already exists")
        
        # Act
        response = client.post(
            "/projects/test-project/adrs?title=Test%20ADR&content=Test%20content"
        )
        
        # Assert
        assert response.status_code == 409
        assert response.json()["detail"] == "ADR with title 'Test ADR' already exists"
    
    def test_get_adr(self):
        """Test getting an ADR by ID."""
        # Arrange
        mock_service.get_adr.return_value = mock_adr
        
        # Act
        response = client.get("/adrs/1")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_adr.assert_called_once_with(1)
        assert response.json() == mock_adr
    
    def test_get_adr_not_found(self):
        """Test getting an ADR that doesn't exist."""
        # Arrange
        mock_service.get_adr.side_effect = NotFoundException("ADR not found")
        
        # Act
        response = client.get("/adrs/1")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "ADR not found"
    
    def test_get_adrs_for_project(self):
        """Test getting all ADRs for a project."""
        # Arrange
        mock_service.get_adrs_for_project.return_value = [mock_adr]
        
        # Act
        response = client.get("/projects/test-project/adrs")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_adrs_for_project.assert_called_once_with("test-project", 0, 100)
        assert response.json() == [mock_adr]
    
    def test_update_adr(self):
        """Test updating an ADR."""
        # Arrange
        mock_service.update_adr.return_value = mock_adr
        
        # Act
        response = client.put(
            "/adrs/1?title=Updated%20ADR&content=Updated%20content"
        )
        
        # Assert
        assert response.status_code == 200
        mock_service.update_adr.assert_called_once_with(1, "Updated ADR", "Updated content")
        assert response.json() == mock_adr
    
    def test_update_adr_not_found(self):
        """Test updating an ADR that doesn't exist."""
        # Arrange
        mock_service.update_adr.side_effect = NotFoundException("ADR not found")
        
        # Act
        response = client.put(
            "/adrs/1?title=Updated%20ADR&content=Updated%20content"
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "ADR not found"
    
    def test_update_adr_title_conflict(self):
        """Test updating an ADR with a title that already exists."""
        # Arrange
        mock_service.update_adr.side_effect = ConflictException("ADR with title 'Updated ADR' already exists")
        
        # Act
        response = client.put(
            "/adrs/1?title=Updated%20ADR&content=Updated%20content"
        )
        
        # Assert
        assert response.status_code == 409
        assert response.json()["detail"] == "ADR with title 'Updated ADR' already exists"
    
    def test_update_adr_no_fields(self):
        """Test updating an ADR with no fields provided."""
        # Arrange
        mock_service.update_adr.side_effect = BadRequestException("No update fields provided")
        
        # Act
        response = client.put("/adrs/1")
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "No update fields provided"
    
    def test_delete_adr(self):
        """Test deleting an ADR."""
        # Arrange
        mock_service.delete_adr.return_value = mock_adr
        
        # Act
        response = client.delete("/adrs/1")
        
        # Assert
        assert response.status_code == 200
        mock_service.delete_adr.assert_called_once_with(1)
        assert response.json() == mock_adr
    
    def test_delete_adr_not_found(self):
        """Test deleting an ADR that doesn't exist."""
        # Arrange
        mock_service.delete_adr.side_effect = NotFoundException("ADR not found")
        
        # Act
        response = client.delete("/adrs/1")
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "ADR not found"
    
    def test_search_adrs(self):
        """Test searching ADRs."""
        # Arrange
        mock_service.search_adrs.return_value = [mock_adr]
        
        # Act
        response = client.get("/projects/test-project/adrs/search?query=test")
        
        # Assert
        assert response.status_code == 200
        mock_service.search_adrs.assert_called_once_with("test-project", "test", 0, 100)
        assert response.json() == [mock_adr]
    
    def test_get_recent_adrs(self):
        """Test getting recent ADRs."""
        # Arrange
        mock_service.get_recent_adrs.return_value = [mock_adr]
        
        # Act
        response = client.get("/projects/test-project/adrs/recent")
        
        # Assert
        assert response.status_code == 200
        mock_service.get_recent_adrs.assert_called_once_with("test-project", 5)
        assert response.json() == [mock_adr]
    
    def test_count_adrs_for_project(self):
        """Test counting ADRs for a project."""
        # Arrange
        mock_service.count_adrs_for_project.return_value = 1
        
        # Act
        response = client.get("/projects/test-project/adrs/count")
        
        # Assert
        assert response.status_code == 200
        mock_service.count_adrs_for_project.assert_called_once_with("test-project")
        assert response.json() == 1
    
    def test_link_adr_to_solution_outline(self):
        """Test linking an ADR to a solution outline."""
        # Act
        response = client.post("/solution-outlines/1/adrs/1")
        
        # Assert
        assert response.status_code == 204