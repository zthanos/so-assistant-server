"""Integration tests for Teams API endpoints.

This module contains integration tests for the Teams API endpoints,
testing the full request-response cycle with a real database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models.projects import Project
from app.domain.models.teams import Team

class TestTeamsAPIIntegration:
    """Integration tests for Teams API endpoints."""
    
    def test_create_team_success(self, client: TestClient, db_session: Session, sample_project_data, sample_team_data):
        """Test creating a team successfully."""
        # First create a project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create team
        response = client.post(
            f"/api/v1/projects/{project.id}/teams",
            json=sample_team_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_team_data["name"]
        assert data["members"] == sample_team_data["members"]
        assert data["project_id"] == project.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify team was created in database
        team = db_session.query(Team).filter(Team.name == sample_team_data["name"]).first()
        assert team is not None
        assert team.project_id == project.id

    def test_create_team_project_not_found(self, client: TestClient):
        """Test creating a team for non-existent project."""
        response = client.post(
            "/api/v1/projects/non-existent-project/teams",
            json={"name": "Test Team", "members": "John Doe"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_create_team_duplicate_name(self, client: TestClient, db_session: Session, sample_project_data, sample_team_data):
        """Test creating a team with duplicate name."""
        # Create project and team
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        team = Team(project_id=project.id, **sample_team_data)
        db_session.add(team)
        db_session.commit()
        
        # Try to create another team with same name
        response = client.post(
            f"/api/v1/projects/{project.id}/teams",
            json=sample_team_data
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["message"].lower()

    def test_get_team_success(self, client: TestClient, db_session: Session, sample_project_data, sample_team_data):
        """Test getting a team successfully."""
        # Create project and team
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        team = Team(project_id=project.id, **sample_team_data)
        db_session.add(team)
        db_session.commit()
        
        # Get team
        response = client.get(f"/api/v1/teams/{team.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == team.id
        assert data["name"] == team.name
        assert data["members"] == team.members
        assert data["project_id"] == team.project_id

    def test_get_team_not_found(self, client: TestClient):
        """Test getting a non-existent team."""
        response = client.get("/api/v1/teams/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_get_teams_for_project_with_pagination(self, client: TestClient, db_session: Session, sample_project_data):
        """Test getting teams for a project with pagination."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create multiple teams
        teams = []
        for i in range(25):
            team = Team(
                project_id=project.id,
                name=f"Team {i+1}",
                members=f"Member {i+1}"
            )
            teams.append(team)
            db_session.add(team)
        db_session.commit()
        
        # Test first page
        response = client.get(f"/api/v1/projects/{project.id}/teams?page=1&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 10
        assert data["meta"]["page"] == 1
        assert data["meta"]["per_page"] == 10
        assert data["meta"]["total"] == 25
        assert data["meta"]["pages"] == 3
        assert data["meta"]["has_next"] is True
        assert data["meta"]["has_prev"] is False
        
        # Test second page
        response = client.get(f"/api/v1/projects/{project.id}/teams?page=2&per_page=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 10
        assert data["meta"]["page"] == 2
        assert data["meta"]["has_next"] is True
        assert data["meta"]["has_prev"] is True

    def test_get_teams_with_search(self, client: TestClient, db_session: Session, sample_project_data):
        """Test getting teams with search functionality."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create teams with different names
        teams_data = [
            {"name": "Frontend Team", "members": "Alice, Bob"},
            {"name": "Backend Team", "members": "Charlie, David"},
            {"name": "DevOps Team", "members": "Eve, Frank"},
            {"name": "QA Team", "members": "Grace, Henry"}
        ]
        
        for team_data in teams_data:
            team = Team(project_id=project.id, **team_data)
            db_session.add(team)
        db_session.commit()
        
        # Search for teams containing "end"
        response = client.get(f"/api/v1/projects/{project.id}/teams?search=end")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2  # Frontend and Backend teams
        
        team_names = [team["name"] for team in data["data"]]
        assert "Frontend Team" in team_names
        assert "Backend Team" in team_names

    def test_update_team_success(self, client: TestClient, db_session: Session, sample_project_data, sample_team_data):
        """Test updating a team successfully."""
        # Create project and team
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        team = Team(project_id=project.id, **sample_team_data)
        db_session.add(team)
        db_session.commit()
        
        # Update team
        update_data = {
            "name": "Updated Team Name",
            "members": "John Doe, Jane Smith, Bob Johnson"
        }
        
        response = client.put(f"/api/v1/teams/{team.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["members"] == update_data["members"]
        
        # Verify update in database
        db_session.refresh(team)
        assert team.name == update_data["name"]
        assert team.members == update_data["members"]

    def test_update_team_not_found(self, client: TestClient):
        """Test updating a non-existent team."""
        response = client.put(
            "/api/v1/teams/999",
            json={"name": "Updated Name"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_delete_team_success(self, client: TestClient, db_session: Session, sample_project_data, sample_team_data):
        """Test deleting a team successfully."""
        # Create project and team
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        team = Team(project_id=project.id, **sample_team_data)
        db_session.add(team)
        db_session.commit()
        team_id = team.id
        
        # Delete team
        response = client.delete(f"/api/v1/teams/{team_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == team_id
        
        # Verify deletion in database
        deleted_team = db_session.query(Team).filter(Team.id == team_id).first()
        assert deleted_team is None

    def test_delete_team_not_found(self, client: TestClient):
        """Test deleting a non-existent team."""
        response = client.delete("/api/v1/teams/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_search_teams_with_pagination(self, client: TestClient, db_session: Session, sample_project_data):
        """Test searching teams with pagination."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create teams with searchable names
        for i in range(15):
            team = Team(
                project_id=project.id,
                name=f"Development Team {i+1}",
                members=f"Developer {i+1}"
            )
            db_session.add(team)
        db_session.commit()
        
        # Search with pagination
        response = client.get(
            f"/api/v1/projects/{project.id}/teams/search?query=Development&page=1&per_page=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 10
        assert data["meta"]["total"] == 15
        assert data["meta"]["pages"] == 2
        assert data["meta"]["has_next"] is True

    def test_count_teams_for_project(self, client: TestClient, db_session: Session, sample_project_data):
        """Test counting teams for a project."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create teams
        for i in range(7):
            team = Team(
                project_id=project.id,
                name=f"Team {i+1}",
                members=f"Member {i+1}"
            )
            db_session.add(team)
        db_session.commit()
        
        # Count teams
        response = client.get(f"/api/v1/projects/{project.id}/teams/count")
        
        assert response.status_code == 200
        assert response.json() == 7

    def test_api_error_responses_format(self, client: TestClient):
        """Test that API error responses follow the standardized format."""
        # Test 404 error
        response = client.get("/api/v1/teams/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "success" in data
        assert data["success"] is False
        assert "message" in data
        assert "error_code" in data
        assert "timestamp" in data

    def test_api_success_responses_format(self, client: TestClient, db_session: Session, sample_project_data):
        """Test that API success responses follow the standardized format."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Test paginated response format
        response = client.get(f"/api/v1/projects/{project.id}/teams")
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "message" in data
        assert "data" in data
        assert "meta" in data
        assert "timestamp" in data
        
        # Check meta structure
        meta = data["meta"]
        assert "page" in meta
        assert "per_page" in meta
        assert "total" in meta
        assert "pages" in meta
        assert "has_next" in meta
        assert "has_prev" in meta