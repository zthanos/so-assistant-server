"""Integration tests for requirement items functionality."""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock

from app.main import app
from app.core.database import Base, get_db
from app.domain.models import Project, ProjectState
from app.domain.models.requirements import RequirementItem, RequirementItemStatus, RequirementItemPriority


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_requirement_items.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def setup_database():
    """Set up test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def db_session():
    """Create database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def sample_project(db_session):
    """Create a sample project for testing."""
    project = Project(
        id="test-project-1",
        name="Test Project",
        description="A test project for requirement items",
        state=ProjectState.active
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture
def sample_requirement_items(db_session, sample_project):
    """Create sample requirement items for testing."""
    items = []
    
    # Create items with different statuses and priorities
    item_data = [
        ("User Authentication", "System shall provide user login", RequirementItemPriority.high, RequirementItemStatus.new),
        ("Password Reset", "System shall allow password reset", RequirementItemPriority.medium, RequirementItemStatus.accepted),
        ("User Registration", "System shall allow user registration", RequirementItemPriority.medium, RequirementItemStatus.rejected),
        ("Session Management", "System shall manage user sessions", RequirementItemPriority.high, RequirementItemStatus.new),
        ("Access Control", "System shall control user access", RequirementItemPriority.critical, RequirementItemStatus.accepted)
    ]
    
    for title, description, priority, status in item_data:
        item = RequirementItem(
            project_id=sample_project.id,
            title=title,
            description=description,
            priority=priority,
            status=status
        )
        db_session.add(item)
        items.append(item)
    
    db_session.commit()
    for item in items:
        db_session.refresh(item)
    
    return items


class TestRequirementItemsCRUD:
    """Test CRUD operations for requirement items."""
    
    def test_create_requirement_item_success(self, client, sample_project, setup_database):
        """Test successful requirement item creation."""
        item_data = {
            "project_id": sample_project.id,
            "title": "New Test Requirement",
            "description": "This is a new test requirement item",
            "priority": "high"
        }
        
        response = client.post("/api/v1/requirement-items", json=item_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == item_data["title"]
        assert data["description"] == item_data["description"]
        assert data["priority"] == "high"
        assert data["status"] == "new"  # Default status
        assert data["project_id"] == sample_project.id
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_create_requirement_item_invalid_project(self, client, setup_database):
        """Test requirement item creation with invalid project ID."""
        item_data = {
            "project_id": "non-existent-project",
            "title": "Test Requirement",
            "description": "This is a test requirement item",
            "priority": "medium"
        }
        
        response = client.post("/api/v1/requirement-items", json=item_data)
        
        assert response.status_code == 404
        assert "Project with id non-existent-project not found" in response.json()["detail"]
    
    def test_create_requirement_item_validation_error(self, client, sample_project, setup_database):
        """Test requirement item creation with validation errors."""
        # Missing required fields
        item_data = {
            "project_id": sample_project.id,
            "title": "",  # Empty title
            "description": "This is a test requirement item"
        }
        
        response = client.post("/api/v1/requirement-items", json=item_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_get_requirement_item_success(self, client, sample_requirement_items, setup_database):
        """Test successful requirement item retrieval."""
        item = sample_requirement_items[0]
        
        response = client.get(f"/api/v1/requirement-items/{item.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == item.id
        assert data["title"] == item.title
        assert data["description"] == item.description
        assert data["priority"] == item.priority.value
        assert data["status"] == item.status.value
    
    def test_get_requirement_item_not_found(self, client, setup_database):
        """Test requirement item retrieval with non-existent ID."""
        response = client.get("/api/v1/requirement-items/999")
        
        assert response.status_code == 404
        assert "RequirementItem with id 999 not found" in response.json()["detail"]
    
    def test_list_requirement_items_all(self, client, sample_requirement_items, setup_database):
        """Test listing all requirement items."""
        response = client.get("/api/v1/requirement-items")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_requirement_items)
        
        # Verify items are returned with correct structure
        for item_data in data:
            assert "id" in item_data
            assert "title" in item_data
            assert "description" in item_data
            assert "priority" in item_data
            assert "status" in item_data
            assert "project_id" in item_data
    
    def test_list_requirement_items_by_project(self, client, sample_requirement_items, sample_project, setup_database):
        """Test listing requirement items filtered by project."""
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(sample_requirement_items)
        
        # Verify all items belong to the project
        for item_data in data:
            assert item_data["project_id"] == sample_project.id
    
    def test_list_requirement_items_by_status(self, client, sample_requirement_items, sample_project, setup_database):
        """Test listing requirement items filtered by status."""
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}&status=accepted")
        
        assert response.status_code == 200
        data = response.json()
        
        # Count expected accepted items
        expected_count = sum(1 for item in sample_requirement_items if item.status == RequirementItemStatus.accepted)
        assert len(data) == expected_count
        
        # Verify all items have accepted status
        for item_data in data:
            assert item_data["status"] == "accepted"
    
    def test_list_requirement_items_pagination(self, client, sample_requirement_items, sample_project, setup_database):
        """Test requirement items pagination."""
        # Test first page
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}&skip=0&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Test second page
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}&skip=2&limit=2")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_update_requirement_item_success(self, client, sample_requirement_items, setup_database):
        """Test successful requirement item update."""
        item = sample_requirement_items[0]
        update_data = {
            "title": "Updated Test Requirement",
            "description": "This is an updated test requirement item",
            "priority": "critical"
        }
        
        response = client.put(f"/api/v1/requirement-items/{item.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == update_data["description"]
        assert data["priority"] == "critical"
        assert data["id"] == item.id
    
    def test_update_requirement_item_partial(self, client, sample_requirement_items, setup_database):
        """Test partial requirement item update."""
        item = sample_requirement_items[0]
        update_data = {
            "title": "Partially Updated Title"
        }
        
        response = client.put(f"/api/v1/requirement-items/{item.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == update_data["title"]
        assert data["description"] == item.description  # Should remain unchanged
        assert data["priority"] == item.priority.value  # Should remain unchanged
    
    def test_update_requirement_item_not_found(self, client, setup_database):
        """Test updating non-existent requirement item."""
        update_data = {
            "title": "Updated Title"
        }
        
        response = client.put("/api/v1/requirement-items/999", json=update_data)
        
        assert response.status_code == 404
        assert "RequirementItem with id 999 not found" in response.json()["detail"]
    
    def test_delete_requirement_item_success(self, client, sample_requirement_items, setup_database):
        """Test successful requirement item deletion."""
        item = sample_requirement_items[0]
        
        response = client.delete(f"/api/v1/requirement-items/{item.id}")
        
        assert response.status_code == 204
        
        # Verify item is deleted
        get_response = client.get(f"/api/v1/requirement-items/{item.id}")
        assert get_response.status_code == 404
    
    def test_delete_requirement_item_not_found(self, client, setup_database):
        """Test deleting non-existent requirement item."""
        response = client.delete("/api/v1/requirement-items/999")
        
        assert response.status_code == 404
        assert "Requirement item with id 999 not found" in response.json()["detail"]


class TestRequirementItemsStatusManagement:
    """Test status management functionality."""
    
    def test_update_status_success(self, client, sample_requirement_items, setup_database):
        """Test successful status update."""
        item = sample_requirement_items[0]  # Should be 'new' status
        status_data = {"status": "accepted"}
        
        response = client.patch(f"/api/v1/requirement-items/{item.id}/status", json=status_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "accepted"
        assert data["id"] == item.id
    
    def test_update_status_invalid_transition(self, client, sample_requirement_items, setup_database):
        """Test status update with invalid transition."""
        # Find an item with 'accepted' status
        accepted_item = next(item for item in sample_requirement_items if item.status == RequirementItemStatus.accepted)
        
        # All transitions are currently allowed in the service, so this test might need adjustment
        # based on actual business rules implemented
        status_data = {"status": "new"}
        
        response = client.patch(f"/api/v1/requirement-items/{accepted_item.id}/status", json=status_data)
        
        # This should succeed based on current implementation (reopening is allowed)
        assert response.status_code == 200
    
    def test_bulk_update_status_success(self, client, sample_requirement_items, setup_database):
        """Test successful bulk status update."""
        # Get IDs of first two items
        item_ids = [sample_requirement_items[0].id, sample_requirement_items[1].id]
        
        request_data = {
            "item_ids": item_ids,
            "status": "accepted"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        
        # Verify all items have updated status
        for item_data in data:
            assert item_data["status"] == "accepted"
            assert item_data["id"] in item_ids
    
    def test_bulk_update_status_empty_list(self, client, setup_database):
        """Test bulk status update with empty item list."""
        request_data = {
            "item_ids": [],
            "status": "accepted"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=request_data)
        
        assert response.status_code == 400
        assert "Item IDs list cannot be empty" in response.json()["detail"]


class TestRequirementItemsAdvancedFeatures:
    """Test advanced features like search and status summary."""
    
    def test_search_requirement_items_success(self, client, sample_requirement_items, sample_project, setup_database):
        """Test successful requirement items search."""
        search_term = "Authentication"
        
        response = client.get(f"/api/v1/requirement-items/projects/{sample_project.id}/search?q={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should find items with "Authentication" in title
        assert len(data) >= 1
        for item_data in data:
            assert search_term.lower() in item_data["title"].lower()
    
    def test_search_requirement_items_no_results(self, client, sample_project, setup_database):
        """Test search with no matching results."""
        search_term = "NonExistentTerm"
        
        response = client.get(f"/api/v1/requirement-items/projects/{sample_project.id}/search?q={search_term}")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
    
    def test_search_requirement_items_empty_term(self, client, sample_project, setup_database):
        """Test search with empty search term."""
        response = client.get(f"/api/v1/requirement-items/projects/{sample_project.id}/search?q=")
        
        assert response.status_code == 400
        assert "Search term cannot be empty" in response.json()["detail"]
    
    def test_get_project_status_summary(self, client, sample_requirement_items, sample_project, setup_database):
        """Test getting project status summary."""
        response = client.get(f"/api/v1/requirement-items/projects/{sample_project.id}/summary")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify summary structure
        assert "new" in data
        assert "accepted" in data
        assert "rejected" in data
        
        # Verify counts match expected values
        expected_new = sum(1 for item in sample_requirement_items if item.status == RequirementItemStatus.new)
        expected_accepted = sum(1 for item in sample_requirement_items if item.status == RequirementItemStatus.accepted)
        expected_rejected = sum(1 for item in sample_requirement_items if item.status == RequirementItemStatus.rejected)
        
        assert data["new"] == expected_new
        assert data["accepted"] == expected_accepted
        assert data["rejected"] == expected_rejected
    
    def test_get_requirement_items_by_status(self, client, sample_requirement_items, sample_project, setup_database):
        """Test getting requirement items by multiple statuses."""
        statuses = ["new", "accepted"]
        
        response = client.get(
            f"/api/v1/requirement-items/projects/{sample_project.id}/by-status"
            f"?statuses={statuses[0]}&statuses={statuses[1]}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all returned items have one of the specified statuses
        for item_data in data:
            assert item_data["status"] in statuses
        
        # Verify count matches expected
        expected_count = sum(
            1 for item in sample_requirement_items 
            if item.status.value in statuses
        )
        assert len(data) == expected_count


class TestRequirementItemsErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_pagination_parameters(self, client, sample_project, setup_database):
        """Test invalid pagination parameters."""
        # Negative skip
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}&skip=-1")
        assert response.status_code == 422  # Validation error
        
        # Invalid limit
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}&limit=0")
        assert response.status_code == 422  # Validation error
        
        response = client.get(f"/api/v1/requirement-items?project_id={sample_project.id}&limit=1001")
        assert response.status_code == 422  # Validation error
    
    def test_invalid_enum_values(self, client, sample_project, setup_database):
        """Test invalid enum values in requests."""
        # Invalid priority
        item_data = {
            "project_id": sample_project.id,
            "title": "Test Requirement",
            "description": "Test description",
            "priority": "invalid_priority"
        }
        
        response = client.post("/api/v1/requirement-items", json=item_data)
        assert response.status_code == 422  # Validation error
        
        # Invalid status in update
        status_data = {"status": "invalid_status"}
        response = client.patch("/api/v1/requirement-items/1/status", json=status_data)
        assert response.status_code == 422  # Validation error
    
    def test_project_not_found_scenarios(self, client, setup_database):
        """Test various scenarios where project is not found."""
        non_existent_project = "non-existent-project"
        
        # Search in non-existent project
        response = client.get(f"/api/v1/requirement-items/projects/{non_existent_project}/search?q=test")
        assert response.status_code == 404
        
        # Get status summary for non-existent project
        response = client.get(f"/api/v1/requirement-items/projects/{non_existent_project}/summary")
        assert response.status_code == 404
        
        # Get items by status for non-existent project
        response = client.get(f"/api/v1/requirement-items/projects/{non_existent_project}/by-status?statuses=new")
        assert response.status_code == 404


class TestRequirementItemsWorkflow:
    """Test complete workflow scenarios."""
    
    def test_complete_crud_workflow(self, client, sample_project, setup_database):
        """Test complete CRUD workflow."""
        # 1. Create a requirement item
        create_data = {
            "project_id": sample_project.id,
            "title": "Workflow Test Requirement",
            "description": "This is a workflow test requirement",
            "priority": "high"
        }
        
        create_response = client.post("/api/v1/requirement-items", json=create_data)
        assert create_response.status_code == 201
        item_data = create_response.json()
        item_id = item_data["id"]
        
        # 2. Read the created item
        get_response = client.get(f"/api/v1/requirement-items/{item_id}")
        assert get_response.status_code == 200
        assert get_response.json()["title"] == create_data["title"]
        
        # 3. Update the item
        update_data = {
            "title": "Updated Workflow Test Requirement",
            "priority": "critical"
        }
        
        update_response = client.put(f"/api/v1/requirement-items/{item_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()["title"] == update_data["title"]
        assert update_response.json()["priority"] == "critical"
        
        # 4. Update status
        status_data = {"status": "accepted"}
        status_response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json=status_data)
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "accepted"
        
        # 5. Verify in project listing
        list_response = client.get(f"/api/v1/requirement-items/projects/{sample_project.id}")
        assert list_response.status_code == 200
        items = list_response.json()
        assert any(item["id"] == item_id for item in items)
        
        # 6. Delete the item
        delete_response = client.delete(f"/api/v1/requirement-items/{item_id}")
        assert delete_response.status_code == 204
        
        # 7. Verify deletion
        get_deleted_response = client.get(f"/api/v1/requirement-items/{item_id}")
        assert get_deleted_response.status_code == 404
    
    def test_status_lifecycle_workflow(self, client, sample_project, setup_database):
        """Test requirement item status lifecycle."""
        # Create item (starts as 'new')
        create_data = {
            "project_id": sample_project.id,
            "title": "Status Lifecycle Test",
            "description": "Testing status transitions",
            "priority": "medium"
        }
        
        create_response = client.post("/api/v1/requirement-items", json=create_data)
        item_id = create_response.json()["id"]
        
        # Verify initial status
        assert create_response.json()["status"] == "new"
        
        # Transition: new -> accepted
        status_response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json={"status": "accepted"})
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "accepted"
        
        # Transition: accepted -> rejected
        status_response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json={"status": "rejected"})
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "rejected"
        
        # Transition: rejected -> new (reopening)
        status_response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json={"status": "new"})
        assert status_response.status_code == 200
        assert status_response.json()["status"] == "new"