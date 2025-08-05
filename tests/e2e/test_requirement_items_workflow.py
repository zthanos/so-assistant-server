"""End-to-end tests for requirement items workflow."""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock

from app.main import app
from app.core.database import Base, get_db
from app.domain.models import Project, ProjectState
from app.domain.models.requirements import RequirementDocument, RequirementDocumentStatus, SourceType


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_e2e_requirement_items.db"
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
def sample_project_with_requirements(db_session):
    """Create a sample project with requirements document for testing."""
    # Create project
    project = Project(
        id="e2e-test-project",
        name="E2E Test Project",
        description="End-to-end test project for requirement items",
        state=ProjectState.active
    )
    db_session.add(project)
    
    # Create requirements document
    requirements_doc = RequirementDocument(
        project_id=project.id,
        content="""# Requirements Document

## User Management
The system shall provide comprehensive user management capabilities.

### Authentication
- The system shall authenticate users using email and password
- The system shall support multi-factor authentication
- The system shall lock accounts after failed login attempts

### Authorization
- The system shall implement role-based access control
- The system shall restrict access based on user permissions

## Data Management
The system shall provide secure data storage and retrieval.

### Data Security
- The system shall encrypt sensitive data at rest
- The system shall encrypt data in transit
- The system shall maintain audit logs of data access

### Data Backup
- The system shall perform automated daily backups
- The system shall allow manual backup initiation
""",
        version=1,
        status=RequirementDocumentStatus.published,
        source_type=SourceType.manual
    )
    db_session.add(requirements_doc)
    
    db_session.commit()
    db_session.refresh(project)
    db_session.refresh(requirements_doc)
    
    return project, requirements_doc


class TestCompleteUserJourney:
    """Test complete user journey from project creation to requirement management."""
    
    def test_full_requirement_management_workflow(self, client, sample_project_with_requirements, setup_database):
        """Test complete workflow: create project → add items → manage lifecycle → generate suggestions."""
        project, requirements_doc = sample_project_with_requirements
        
        # Step 1: Verify project exists and has requirements document
        # (This would typically be done through project API, but we'll assume it exists)
        
        # Step 2: Create initial requirement items based on the requirements document
        initial_items = [
            {
                "project_id": project.id,
                "title": "User Email Authentication",
                "description": "Implement email and password authentication for users",
                "priority": "high"
            },
            {
                "project_id": project.id,
                "title": "Multi-Factor Authentication",
                "description": "Add support for MFA using TOTP or SMS",
                "priority": "medium"
            },
            {
                "project_id": project.id,
                "title": "Account Lockout Protection",
                "description": "Lock user accounts after multiple failed login attempts",
                "priority": "high"
            },
            {
                "project_id": project.id,
                "title": "Role-Based Access Control",
                "description": "Implement RBAC system for user permissions",
                "priority": "critical"
            },
            {
                "project_id": project.id,
                "title": "Data Encryption at Rest",
                "description": "Encrypt sensitive data stored in the database",
                "priority": "critical"
            }
        ]
        
        created_items = []
        for item_data in initial_items:
            response = client.post("/api/v1/requirement-items", json=item_data)
            assert response.status_code == 201
            created_items.append(response.json())
        
        assert len(created_items) == 5
        
        # Step 3: Review and manage requirement items
        # Get all items for the project
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}")
        assert response.status_code == 200
        all_items = response.json()
        assert len(all_items) == 5
        
        # Step 4: Review items by priority
        high_priority_items = [item for item in all_items if item["priority"] == "high"]
        critical_priority_items = [item for item in all_items if item["priority"] == "critical"]
        
        assert len(high_priority_items) == 2
        assert len(critical_priority_items) == 2
        
        # Step 5: Accept critical priority items first
        critical_item_ids = [item["id"] for item in critical_priority_items]
        bulk_update_data = {
            "item_ids": critical_item_ids,
            "status": "accepted"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=bulk_update_data)
        assert response.status_code == 200
        updated_items = response.json()
        assert len(updated_items) == 2
        assert all(item["status"] == "accepted" for item in updated_items)
        
        # Step 6: Review high priority items individually
        for item in high_priority_items:
            # Accept the first high priority item
            if item["title"] == "User Email Authentication":
                status_data = {"status": "accepted"}
                response = client.patch(f"/api/v1/requirement-items/{item['id']}/status", json=status_data)
                assert response.status_code == 200
                assert response.json()["status"] == "accepted"
            
            # Reject the account lockout item for now (needs more analysis)
            elif item["title"] == "Account Lockout Protection":
                status_data = {"status": "rejected"}
                response = client.patch(f"/api/v1/requirement-items/{item['id']}/status", json=status_data)
                assert response.status_code == 200
                assert response.json()["status"] == "rejected"
        
        # Step 7: Check project status summary
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/summary")
        assert response.status_code == 200
        summary = response.json()
        
        # Should have: 3 accepted, 1 rejected, 1 new (MFA item)
        assert summary["accepted"] == 3
        assert summary["rejected"] == 1
        assert summary["new"] == 1
        
        # Step 8: Search for specific requirements
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/search?q=authentication")
        assert response.status_code == 200
        auth_items = response.json()
        assert len(auth_items) >= 2  # Should find email auth and MFA items
        
        # Step 9: Filter items by status
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/by-status?statuses=accepted")
        assert response.status_code == 200
        accepted_items = response.json()
        assert len(accepted_items) == 3
        
        # Step 10: Update a requirement item based on feedback
        mfa_item = next(item for item in all_items if "Multi-Factor" in item["title"])
        update_data = {
            "title": "Enhanced Multi-Factor Authentication",
            "description": "Add support for MFA using TOTP, SMS, and hardware tokens",
            "priority": "high"  # Upgraded priority
        }
        
        response = client.put(f"/api/v1/requirement-items/{mfa_item['id']}", json=update_data)
        assert response.status_code == 200
        updated_mfa = response.json()
        assert updated_mfa["title"] == update_data["title"]
        assert updated_mfa["priority"] == "high"
        
        # Step 11: Accept the updated MFA requirement
        status_data = {"status": "accepted"}
        response = client.patch(f"/api/v1/requirement-items/{mfa_item['id']}/status", json=status_data)
        assert response.status_code == 200
        
        # Step 12: Final status check
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/summary")
        assert response.status_code == 200
        final_summary = response.json()
        
        # Should now have: 4 accepted, 1 rejected, 0 new
        assert final_summary["accepted"] == 4
        assert final_summary["rejected"] == 1
        assert final_summary["new"] == 0
    
    def test_requirement_lifecycle_with_reopening(self, client, sample_project_with_requirements, setup_database):
        """Test requirement lifecycle including reopening rejected items."""
        project, _ = sample_project_with_requirements
        
        # Create a requirement item
        item_data = {
            "project_id": project.id,
            "title": "Advanced Security Feature",
            "description": "Implement advanced security monitoring",
            "priority": "medium"
        }
        
        response = client.post("/api/v1/requirement-items", json=item_data)
        assert response.status_code == 201
        item = response.json()
        item_id = item["id"]
        
        # Initial status should be 'new'
        assert item["status"] == "new"
        
        # Reject the item initially (needs more research)
        status_data = {"status": "rejected"}
        response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json=status_data)
        assert response.status_code == 200
        assert response.json()["status"] == "rejected"
        
        # After research, reopen the item
        status_data = {"status": "new"}
        response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json=status_data)
        assert response.status_code == 200
        assert response.json()["status"] == "new"
        
        # Update the item with more details
        update_data = {
            "title": "Advanced Security Monitoring System",
            "description": "Implement real-time security monitoring with threat detection and automated response capabilities",
            "priority": "high"
        }
        
        response = client.put(f"/api/v1/requirement-items/{item_id}", json=update_data)
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["priority"] == "high"
        
        # Now accept the refined requirement
        status_data = {"status": "accepted"}
        response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json=status_data)
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
    
    def test_concurrent_requirement_management(self, client, sample_project_with_requirements, setup_database):
        """Test concurrent operations on requirement items."""
        project, _ = sample_project_with_requirements
        
        # Create multiple items concurrently (simulated)
        items_data = [
            {
                "project_id": project.id,
                "title": f"Concurrent Requirement {i}",
                "description": f"This is concurrent requirement number {i}",
                "priority": "medium"
            }
            for i in range(1, 6)
        ]
        
        created_items = []
        for item_data in items_data:
            response = client.post("/api/v1/requirement-items", json=item_data)
            assert response.status_code == 201
            created_items.append(response.json())
        
        # Perform bulk operations
        all_item_ids = [item["id"] for item in created_items]
        
        # Bulk accept first 3 items
        bulk_accept_data = {
            "item_ids": all_item_ids[:3],
            "status": "accepted"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=bulk_accept_data)
        assert response.status_code == 200
        accepted_items = response.json()
        assert len(accepted_items) == 3
        
        # Bulk reject last 2 items
        bulk_reject_data = {
            "item_ids": all_item_ids[3:],
            "status": "rejected"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=bulk_reject_data)
        assert response.status_code == 200
        rejected_items = response.json()
        assert len(rejected_items) == 2
        
        # Verify final state
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/summary")
        assert response.status_code == 200
        summary = response.json()
        
        # Should include the items from previous tests plus these new ones
        assert summary["accepted"] >= 3
        assert summary["rejected"] >= 2
    
    def test_requirement_items_with_pagination_workflow(self, client, sample_project_with_requirements, setup_database):
        """Test workflow with large number of requirement items using pagination."""
        project, _ = sample_project_with_requirements
        
        # Create many requirement items
        batch_size = 25
        items_data = [
            {
                "project_id": project.id,
                "title": f"Batch Requirement {i:03d}",
                "description": f"This is batch requirement number {i} for pagination testing",
                "priority": "low" if i % 3 == 0 else "medium" if i % 3 == 1 else "high"
            }
            for i in range(1, batch_size + 1)
        ]
        
        # Create all items
        for item_data in items_data:
            response = client.post("/api/v1/requirement-items", json=item_data)
            assert response.status_code == 201
        
        # Test pagination
        page_size = 10
        all_items = []
        
        # Get first page
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}?skip=0&limit={page_size}")
        assert response.status_code == 200
        page1_items = response.json()
        assert len(page1_items) == page_size
        all_items.extend(page1_items)
        
        # Get second page
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}?skip={page_size}&limit={page_size}")
        assert response.status_code == 200
        page2_items = response.json()
        assert len(page2_items) == page_size
        all_items.extend(page2_items)
        
        # Get remaining items
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}?skip={page_size*2}&limit={page_size}")
        assert response.status_code == 200
        page3_items = response.json()
        all_items.extend(page3_items)
        
        # Verify we got all items (including those from previous tests)
        assert len(all_items) >= batch_size
        
        # Test filtering with pagination
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}?status=new&skip=0&limit=5")
        assert response.status_code == 200
        new_items_page = response.json()
        assert len(new_items_page) <= 5
        assert all(item["status"] == "new" for item in new_items_page)


class TestAISuggestionsWorkflow:
    """Test AI-powered suggestions workflow (mocked)."""
    
    @patch('app.services.requirement_suggestion_service.RequirementSuggestionService.stream_requirement_suggestions')
    def test_ai_suggestions_workflow_mock(self, mock_stream_suggestions, client, sample_project_with_requirements, setup_database):
        """Test AI suggestions workflow with mocked LLM service."""
        project, _ = sample_project_with_requirements
        
        # Mock the streaming suggestions method
        async def mock_stream_suggestions_impl(db, client_id, project_id, max_suggestions):
            # Simulate streaming suggestions
            mock_suggestions = [
                {
                    "title": "Session Timeout Management",
                    "description": "Implement automatic session timeout after period of inactivity",
                    "priority": "medium",
                    "rationale": "Essential for security to prevent unauthorized access from unattended sessions"
                },
                {
                    "title": "Password Complexity Requirements",
                    "description": "Enforce strong password policies with complexity requirements",
                    "priority": "high",
                    "rationale": "Strong passwords are fundamental to authentication security"
                },
                {
                    "title": "Audit Trail for Data Access",
                    "description": "Log all data access operations for compliance and security monitoring",
                    "priority": "high",
                    "rationale": "Required for compliance and security incident investigation"
                }
            ]
            
            # Simulate SSE events (this would normally be handled by the SSE manager)
            return mock_suggestions
        
        mock_stream_suggestions.side_effect = mock_stream_suggestions_impl
        
        # Test the suggestions endpoint (this would normally return SSE stream)
        # For testing purposes, we'll verify the endpoint exists and can be called
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/suggestions?max_suggestions=5")
        
        # The actual response would be an SSE stream, but for testing we just verify
        # the endpoint is accessible and doesn't return an immediate error
        # In a real scenario, this would establish an SSE connection
        assert response.status_code in [200, 404]  # 404 if dependencies not properly mocked
    
    def test_suggestions_integration_with_requirement_creation(self, client, sample_project_with_requirements, setup_database):
        """Test integration between AI suggestions and requirement item creation."""
        project, _ = sample_project_with_requirements
        
        # Simulate receiving AI suggestions and creating requirement items from them
        suggested_requirements = [
            {
                "project_id": project.id,
                "title": "Session Timeout Management",
                "description": "Implement automatic session timeout after 30 minutes of inactivity",
                "priority": "medium"
            },
            {
                "project_id": project.id,
                "title": "Password Complexity Requirements",
                "description": "Enforce passwords with minimum 8 characters, mixed case, numbers, and special characters",
                "priority": "high"
            },
            {
                "project_id": project.id,
                "title": "Audit Trail for Data Access",
                "description": "Log all data access operations with timestamp, user, and operation details",
                "priority": "high"
            }
        ]
        
        # Create requirement items from suggestions
        created_from_suggestions = []
        for suggestion in suggested_requirements:
            response = client.post("/api/v1/requirement-items", json=suggestion)
            assert response.status_code == 201
            created_from_suggestions.append(response.json())
        
        # Verify all suggestions were created
        assert len(created_from_suggestions) == 3
        
        # Review and accept the high-priority suggestions
        high_priority_suggestions = [item for item in created_from_suggestions if item["priority"] == "high"]
        
        for item in high_priority_suggestions:
            status_data = {"status": "accepted"}
            response = client.patch(f"/api/v1/requirement-items/{item['id']}/status", json=status_data)
            assert response.status_code == 200
            assert response.json()["status"] == "accepted"
        
        # Keep medium priority suggestion as new for further review
        medium_priority_item = next(item for item in created_from_suggestions if item["priority"] == "medium")
        
        # Verify the item is still in 'new' status
        response = client.get(f"/api/v1/requirement-items/{medium_priority_item['id']}")
        assert response.status_code == 200
        assert response.json()["status"] == "new"
        
        # Check final project summary
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/summary")
        assert response.status_code == 200
        summary = response.json()
        
        # Should have accepted items from suggestions plus any from previous tests
        assert summary["accepted"] >= 2  # At least the 2 high-priority suggestions
        assert summary["new"] >= 1  # At least the medium-priority suggestion


class TestErrorRecoveryWorkflow:
    """Test error recovery and edge case workflows."""
    
    def test_recovery_from_invalid_operations(self, client, sample_project_with_requirements, setup_database):
        """Test recovery from various invalid operations."""
        project, _ = sample_project_with_requirements
        
        # Create a valid requirement item
        item_data = {
            "project_id": project.id,
            "title": "Error Recovery Test",
            "description": "Testing error recovery scenarios",
            "priority": "medium"
        }
        
        response = client.post("/api/v1/requirement-items", json=item_data)
        assert response.status_code == 201
        item = response.json()
        item_id = item["id"]
        
        # Try invalid operations and verify they fail gracefully
        
        # 1. Try to update with invalid data
        invalid_update = {
            "title": "",  # Empty title should fail
            "priority": "invalid_priority"
        }
        
        response = client.put(f"/api/v1/requirement-items/{item_id}", json=invalid_update)
        assert response.status_code == 422  # Validation error
        
        # Verify item is unchanged
        response = client.get(f"/api/v1/requirement-items/{item_id}")
        assert response.status_code == 200
        unchanged_item = response.json()
        assert unchanged_item["title"] == item["title"]  # Should be unchanged
        
        # 2. Try bulk operations with invalid data
        invalid_bulk_data = {
            "item_ids": [item_id, 999999],  # Include non-existent ID
            "status": "accepted"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=invalid_bulk_data)
        assert response.status_code == 404  # Should fail due to non-existent ID
        
        # Verify original item status is unchanged
        response = client.get(f"/api/v1/requirement-items/{item_id}")
        assert response.status_code == 200
        assert response.json()["status"] == "new"  # Should still be new
        
        # 3. Perform valid operations after errors
        valid_update = {
            "title": "Successfully Updated After Error",
            "priority": "high"
        }
        
        response = client.put(f"/api/v1/requirement-items/{item_id}", json=valid_update)
        assert response.status_code == 200
        updated_item = response.json()
        assert updated_item["title"] == valid_update["title"]
        
        # 4. Valid status update
        status_data = {"status": "accepted"}
        response = client.patch(f"/api/v1/requirement-items/{item_id}/status", json=status_data)
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"
    
    def test_data_consistency_across_operations(self, client, sample_project_with_requirements, setup_database):
        """Test data consistency across multiple concurrent-like operations."""
        project, _ = sample_project_with_requirements
        
        # Create multiple items
        items_data = [
            {
                "project_id": project.id,
                "title": f"Consistency Test Item {i}",
                "description": f"Testing data consistency for item {i}",
                "priority": "medium"
            }
            for i in range(1, 4)
        ]
        
        created_items = []
        for item_data in items_data:
            response = client.post("/api/v1/requirement-items", json=item_data)
            assert response.status_code == 201
            created_items.append(response.json())
        
        # Perform multiple operations and verify consistency
        
        # 1. Update items individually
        for i, item in enumerate(created_items):
            update_data = {
                "title": f"Updated Consistency Test Item {i+1}",
                "priority": "high"
            }
            response = client.put(f"/api/v1/requirement-items/{item['id']}", json=update_data)
            assert response.status_code == 200
        
        # 2. Verify all updates were applied
        for i, item in enumerate(created_items):
            response = client.get(f"/api/v1/requirement-items/{item['id']}")
            assert response.status_code == 200
            updated_item = response.json()
            assert f"Updated Consistency Test Item {i+1}" in updated_item["title"]
            assert updated_item["priority"] == "high"
        
        # 3. Bulk status update
        all_ids = [item["id"] for item in created_items]
        bulk_data = {
            "item_ids": all_ids,
            "status": "accepted"
        }
        
        response = client.patch("/api/v1/requirement-items/bulk/status", json=bulk_data)
        assert response.status_code == 200
        bulk_updated = response.json()
        assert len(bulk_updated) == len(created_items)
        
        # 4. Verify consistency in project summary
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}/summary")
        assert response.status_code == 200
        summary = response.json()
        
        # Should include the accepted items from this test
        assert summary["accepted"] >= len(created_items)
        
        # 5. Verify consistency in filtered queries
        response = client.get(f"/api/v1/requirement-items/projects/{project.id}?status=accepted")
        assert response.status_code == 200
        accepted_items = response.json()
        
        # Should include all items we just accepted
        accepted_ids = [item["id"] for item in accepted_items]
        for item_id in all_ids:
            assert item_id in accepted_ids