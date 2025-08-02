"""Integration tests for ADRs API endpoints.

This module contains integration tests for the Architecture Decision Records (ADRs) API endpoints,
testing the full request-response cycle with a real database.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.domain.models.projects import Project
from app.domain.models.adrs import ADR

class TestADRsAPIIntegration:
    """Integration tests for ADRs API endpoints."""
    
    def test_create_adr_success(self, client: TestClient, db_session: Session, sample_project_data, sample_adr_data):
        """Test creating an ADR successfully."""
        # First create a project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create ADR
        response = client.post(
            f"/api/v1/projects/{project.id}/adrs",
            params={
                "title": sample_adr_data["title"],
                "content": sample_adr_data["content"]
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_adr_data["title"]
        assert data["content"] == sample_adr_data["content"]
        assert data["project_id"] == project.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify ADR was created in database
        adr = db_session.query(ADR).filter(ADR.title == sample_adr_data["title"]).first()
        assert adr is not None
        assert adr.project_id == project.id

    def test_create_adr_project_not_found(self, client: TestClient):
        """Test creating an ADR for non-existent project."""
        response = client.post(
            "/api/v1/projects/non-existent-project/adrs",
            params={
                "title": "Test ADR",
                "content": "Test content"
            }
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_create_adr_duplicate_title(self, client: TestClient, db_session: Session, sample_project_data, sample_adr_data):
        """Test creating an ADR with duplicate title."""
        # Create project and ADR
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        adr = ADR(project_id=project.id, **sample_adr_data)
        db_session.add(adr)
        db_session.commit()
        
        # Try to create another ADR with same title
        response = client.post(
            f"/api/v1/projects/{project.id}/adrs",
            params={
                "title": sample_adr_data["title"],
                "content": "Different content"
            }
        )
        
        assert response.status_code == 409
        data = response.json()
        assert "already exists" in data["message"].lower()

    def test_get_adr_success(self, client: TestClient, db_session: Session, sample_project_data, sample_adr_data):
        """Test getting an ADR successfully."""
        # Create project and ADR
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        adr = ADR(project_id=project.id, **sample_adr_data)
        db_session.add(adr)
        db_session.commit()
        
        # Get ADR
        response = client.get(f"/api/v1/adrs/{adr.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == adr.id
        assert data["title"] == adr.title
        assert data["content"] == adr.content
        assert data["project_id"] == adr.project_id

    def test_get_adr_not_found(self, client: TestClient):
        """Test getting a non-existent ADR."""
        response = client.get("/api/v1/adrs/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_get_adrs_for_project_with_pagination(self, client: TestClient, db_session: Session, sample_project_data):
        """Test getting ADRs for a project with pagination."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create multiple ADRs
        adrs = []
        for i in range(25):
            adr = ADR(
                project_id=project.id,
                title=f"ADR {i+1}",
                content=f"Content for ADR {i+1}"
            )
            adrs.append(adr)
            db_session.add(adr)
        db_session.commit()
        
        # Test first page
        response = client.get(f"/api/v1/projects/{project.id}/adrs?page=1&per_page=10")
        
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

    def test_get_adrs_with_search(self, client: TestClient, db_session: Session, sample_project_data):
        """Test getting ADRs with search functionality."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create ADRs with different titles and content
        adrs_data = [
            {"title": "Database Selection", "content": "We chose PostgreSQL for our database"},
            {"title": "API Framework", "content": "FastAPI was selected for the API framework"},
            {"title": "Authentication Method", "content": "JWT tokens for authentication"},
            {"title": "Database Migration", "content": "Alembic for database migrations"}
        ]
        
        for adr_data in adrs_data:
            adr = ADR(project_id=project.id, **adr_data)
            db_session.add(adr)
        db_session.commit()
        
        # Search for ADRs containing "database"
        response = client.get(f"/api/v1/projects/{project.id}/adrs?search=database")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 2  # Database Selection and Database Migration
        
        adr_titles = [adr["title"] for adr in data["data"]]
        assert "Database Selection" in adr_titles
        assert "Database Migration" in adr_titles

    def test_update_adr_success(self, client: TestClient, db_session: Session, sample_project_data, sample_adr_data):
        """Test updating an ADR successfully."""
        # Create project and ADR
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        adr = ADR(project_id=project.id, **sample_adr_data)
        db_session.add(adr)
        db_session.commit()
        
        # Update ADR
        response = client.put(
            f"/api/v1/adrs/{adr.id}",
            params={
                "title": "Updated ADR Title",
                "content": "Updated ADR content with more details"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated ADR Title"
        assert data["content"] == "Updated ADR content with more details"
        
        # Verify update in database
        db_session.refresh(adr)
        assert adr.title == "Updated ADR Title"
        assert adr.content == "Updated ADR content with more details"

    def test_update_adr_not_found(self, client: TestClient):
        """Test updating a non-existent ADR."""
        response = client.put(
            "/api/v1/adrs/999",
            params={"title": "Updated Title"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_delete_adr_success(self, client: TestClient, db_session: Session, sample_project_data, sample_adr_data):
        """Test deleting an ADR successfully."""
        # Create project and ADR
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        adr = ADR(project_id=project.id, **sample_adr_data)
        db_session.add(adr)
        db_session.commit()
        adr_id = adr.id
        
        # Delete ADR
        response = client.delete(f"/api/v1/adrs/{adr_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == adr_id
        
        # Verify deletion in database
        deleted_adr = db_session.query(ADR).filter(ADR.id == adr_id).first()
        assert deleted_adr is None

    def test_delete_adr_not_found(self, client: TestClient):
        """Test deleting a non-existent ADR."""
        response = client.delete("/api/v1/adrs/999")
        
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["message"].lower()

    def test_search_adrs_with_pagination(self, client: TestClient, db_session: Session, sample_project_data):
        """Test searching ADRs with pagination."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create ADRs with searchable content
        for i in range(15):
            adr = ADR(
                project_id=project.id,
                title=f"Architecture Decision {i+1}",
                content=f"This is an architecture decision about component {i+1}"
            )
            db_session.add(adr)
        db_session.commit()
        
        # Search with pagination
        response = client.get(
            f"/api/v1/projects/{project.id}/adrs/search?query=architecture&page=1&per_page=10"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 10
        assert data["meta"]["total"] == 15
        assert data["meta"]["pages"] == 2
        assert data["meta"]["has_next"] is True

    def test_get_recent_adrs(self, client: TestClient, db_session: Session, sample_project_data):
        """Test getting recent ADRs for a project."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create ADRs
        for i in range(10):
            adr = ADR(
                project_id=project.id,
                title=f"ADR {i+1}",
                content=f"Content {i+1}"
            )
            db_session.add(adr)
        db_session.commit()
        
        # Get recent ADRs (default limit is 5)
        response = client.get(f"/api/v1/projects/{project.id}/adrs/recent")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5  # Should return at most 5 recent ADRs

    def test_count_adrs_for_project(self, client: TestClient, db_session: Session, sample_project_data):
        """Test counting ADRs for a project."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create ADRs
        for i in range(8):
            adr = ADR(
                project_id=project.id,
                title=f"ADR {i+1}",
                content=f"Content {i+1}"
            )
            db_session.add(adr)
        db_session.commit()
        
        # Count ADRs
        response = client.get(f"/api/v1/projects/{project.id}/adrs/count")
        
        assert response.status_code == 200
        assert response.json() == 8

    def test_filtering_adrs_by_date(self, client: TestClient, db_session: Session, sample_project_data):
        """Test filtering ADRs by creation date."""
        # Create project
        project = Project(**sample_project_data)
        db_session.add(project)
        db_session.commit()
        
        # Create ADRs
        for i in range(5):
            adr = ADR(
                project_id=project.id,
                title=f"ADR {i+1}",
                content=f"Content {i+1}"
            )
            db_session.add(adr)
        db_session.commit()
        
        # Test filtering (this would work with proper date filtering implementation)
        response = client.get(f"/api/v1/projects/{project.id}/adrs?sort_by=created_at&sort_order=desc")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 5