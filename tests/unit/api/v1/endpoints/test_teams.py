"""Tests for the Team API endpoints.

This module contains unit tests for the Team API endpoints.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.api.v1.endpoints.teams import router
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Mock service
mock_service = MagicMock()

# Mock team
mock_team = {
    "id": 1,
    "project_id": "test-project",
    "name": "Test Team",
    "members": "John Doe, Jane Smith",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

mock_teams = [
    mock_team,
    {
        "id": 2,
        "project_id": "test-project",
        "name": "Another Team",
        "members": "Alice, Bob",
        "created_at": "2023-01-01T00:00:00",
        "updated_at": "2023-01-01T00:00:00"
    }
]

# Override dependencies
@pytest.fixture(autouse=True)
def override_dependencies():
    """Override dependencies for testing."""
    with patch("app.api.v1.endpoints.teams.get_team_service", return_value=mock_service):
        yield

class TestTeamEndpoints:
    """Test cases for the Team API endpoints."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Reset mock
        mock_service.reset_mock()

    def test_create_team(self):
        """Test creating a team."""
        # Arrange
        mock_service.create_team.return_value = mock_team
        
        # Act
        response = client.post(
            "/projects/test-project/teams",
            json={"name": "Test Team", "members": "John Doe, Jane Smith"}
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json() == mock_team
        mock_service.create_team.assert_called_once_with(
            "test-project", "Test Team", "John Doe, Jane Smith"
        )

    def test_create_team_project_not_found(self):
        """Test creating a team with a non-existent project."""
        # Arrange
        mock_service.create_team.side_effect = NotFoundException(
            "Project with ID test-project not found", resource_type="Project"
        )
        
        # Act
        response = client.post(
            "/api/v1/projects/test-project/teams",
            json={"name": "Test Team", "members": "John Doe, Jane Smith"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_create_team_conflict(self):
        """Test creating a team with a name that already exists."""
        # Arrange
        mock_service.create_team.side_effect = ConflictException(
            "Team with name 'Test Team' already exists for project test-project",
            resource_type="Team"
        )
        
        # Act
        response = client.post(
            "/api/v1/projects/test-project/teams",
            json={"name": "Test Team", "members": "John Doe, Jane Smith"}
        )
        
        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_get_team(self):
        """Test getting a team by ID."""
        # Arrange
        mock_service.get_team.return_value = mock_team
        
        # Act
        response = client.get("/api/v1/teams/1")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_team
        mock_service.get_team.assert_called_once_with(1)

    def test_get_team_not_found(self):
        """Test getting a non-existent team."""
        # Arrange
        mock_service.get_team.side_effect = NotFoundException(
            "Team with ID 1 not found", resource_type="Team"
        )
        
        # Act
        response = client.get("/api/v1/teams/1")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_team_with_tasks(self):
        """Test getting a team with its tasks."""
        # Arrange
        mock_service.get_team_with_tasks.return_value = mock_team
        
        # Act
        response = client.get("/api/v1/teams/1/with-tasks")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_team
        mock_service.get_team_with_tasks.assert_called_once_with(1)

    def test_get_teams_for_project(self):
        """Test getting all teams for a project."""
        # Arrange
        mock_service.get_teams_for_project.return_value = mock_teams
        
        # Act
        response = client.get("/api/v1/projects/test-project/teams")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_teams
        mock_service.get_teams_for_project.assert_called_once_with("test-project", 0, 100)

    def test_update_team(self):
        """Test updating a team."""
        # Arrange
        mock_service.update_team.return_value = mock_team
        
        # Act
        response = client.put(
            "/api/v1/teams/1",
            json={"name": "Updated Team", "members": "John Doe, Jane Smith, Alice"}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_team
        mock_service.update_team.assert_called_once_with(1, "Updated Team", "John Doe, Jane Smith, Alice")

    def test_update_team_not_found(self):
        """Test updating a non-existent team."""
        # Arrange
        mock_service.update_team.side_effect = NotFoundException(
            "Team with ID 1 not found", resource_type="Team"
        )
        
        # Act
        response = client.put(
            "/api/v1/teams/1",
            json={"name": "Updated Team", "members": "John Doe, Jane Smith, Alice"}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_team_conflict(self):
        """Test updating a team with a name that already exists."""
        # Arrange
        mock_service.update_team.side_effect = ConflictException(
            "Team with name 'Updated Team' already exists for project test-project",
            resource_type="Team"
        )
        
        # Act
        response = client.put(
            "/api/v1/teams/1",
            json={"name": "Updated Team", "members": "John Doe, Jane Smith, Alice"}
        )
        
        # Assert
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_update_team_bad_request(self):
        """Test updating a team with no update fields."""
        # Arrange
        mock_service.update_team.side_effect = BadRequestException(
            "No update fields provided"
        )
        
        # Act
        response = client.put(
            "/api/v1/teams/1",
            json={"name": None, "members": None}
        )
        
        # Assert
        assert response.status_code == 400
        assert "No update fields" in response.json()["detail"]

    def test_delete_team(self):
        """Test deleting a team."""
        # Arrange
        mock_service.delete_team.return_value = mock_team
        
        # Act
        response = client.delete("/api/v1/teams/1")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_team
        mock_service.delete_team.assert_called_once_with(1)

    def test_delete_team_not_found(self):
        """Test deleting a non-existent team."""
        # Arrange
        mock_service.delete_team.side_effect = NotFoundException(
            "Team with ID 1 not found", resource_type="Team"
        )
        
        # Act
        response = client.delete("/api/v1/teams/1")
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_search_teams(self):
        """Test searching teams."""
        # Arrange
        mock_service.search_teams.return_value = mock_teams
        
        # Act
        response = client.get("/api/v1/projects/test-project/teams/search?query=Test")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == mock_teams
        mock_service.search_teams.assert_called_once_with("test-project", "Test", 0, 100)

    def test_count_teams_for_project(self):
        """Test counting teams for a project."""
        # Arrange
        mock_service.count_teams_for_project.return_value = 2
        
        # Act
        response = client.get("/api/v1/projects/test-project/teams/count")
        
        # Assert
        assert response.status_code == 200
        assert response.json() == 2
        mock_service.count_teams_for_project.assert_called_once_with("test-project")