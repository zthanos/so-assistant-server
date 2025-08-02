"""End-to-end test configuration and fixtures.

This module provides fixtures and configuration for end-to-end tests
that test complete workflows across the entire application.
"""
import pytest
import asyncio
import tempfile
import os
from typing import Generator, Dict, Any, List
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import get_db, Base
from app.api.dependencies import get_sse_manager

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def sse_manager():
    """Create a fresh SSE manager for each test."""
    from app.core.events import SSEManager
    return SSEManager()

@pytest.fixture(scope="function")
def client_with_sse(db_session, sse_manager):
    """Create a test client with both database and SSE manager overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    def override_get_sse_manager():
        return sse_manager
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_sse_manager] = override_get_sse_manager
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Clean up
    app.dependency_overrides.clear()

# Workflow test data fixtures
@pytest.fixture
def project_workflow_data():
    """Complete project data for workflow testing."""
    return {
        "project": {
            "id": "e2e-test-project",
            "name": "E2E Test Project",
            "description": "A comprehensive project for end-to-end testing",
            "code": "E2E001",
            "state": "active"
        },
        "teams": [
            {
                "name": "Frontend Team",
                "members": "Alice Johnson, Bob Smith"
            },
            {
                "name": "Backend Team", 
                "members": "Charlie Brown, Diana Prince"
            },
            {
                "name": "DevOps Team",
                "members": "Eve Wilson, Frank Miller"
            }
        ],
        "adrs": [
            {
                "title": "Frontend Framework Selection",
                "content": "We have decided to use React for our frontend framework due to its component-based architecture and strong ecosystem."
            },
            {
                "title": "Database Choice",
                "content": "PostgreSQL has been selected as our primary database for its reliability and advanced features."
            },
            {
                "title": "API Design Standards",
                "content": "We will follow REST principles with OpenAPI documentation for all our API endpoints."
            }
        ],
        "solution_outline": {
            "content": """# Solution Outline for E2E Test Project

## Overview
This is a comprehensive solution outline for testing end-to-end workflows.

## Architecture
- Frontend: React application
- Backend: FastAPI with Python
- Database: PostgreSQL
- Authentication: JWT tokens

## Implementation Plan
1. Set up development environment
2. Implement core API endpoints
3. Build frontend components
4. Add authentication system
5. Deploy to staging environment

## Testing Strategy
- Unit tests for individual components
- Integration tests for API endpoints
- End-to-end tests for user workflows
""",
            "status": "draft"
        }
    }

@pytest.fixture
def user_workflow_scenarios():
    """Different user workflow scenarios for testing."""
    return {
        "project_manager": {
            "role": "Project Manager",
            "workflows": [
                "create_project",
                "manage_teams",
                "review_solution_outline",
                "track_progress"
            ]
        },
        "architect": {
            "role": "Solution Architect", 
            "workflows": [
                "create_adrs",
                "design_solution_outline",
                "review_technical_decisions",
                "update_architecture"
            ]
        },
        "developer": {
            "role": "Developer",
            "workflows": [
                "view_project_details",
                "check_team_assignments",
                "read_adrs",
                "implement_features"
            ]
        }
    }

@pytest.fixture
def workflow_test_helpers():
    """Helper functions for workflow testing."""
    class WorkflowHelpers:
        @staticmethod
        def create_complete_project(client: TestClient, project_data: Dict[str, Any]) -> Dict[str, Any]:
            """Create a complete project with all associated data."""
            results = {}
            
            # Create project
            project_response = client.post("/api/v1/projects", json=project_data["project"])
            assert project_response.status_code == 201
            results["project"] = project_response.json()
            
            # Create teams
            results["teams"] = []
            for team_data in project_data["teams"]:
                team_response = client.post(
                    f"/api/v1/projects/{project_data['project']['id']}/teams",
                    json=team_data
                )
                assert team_response.status_code == 201
                results["teams"].append(team_response.json())
            
            # Create ADRs
            results["adrs"] = []
            for adr_data in project_data["adrs"]:
                adr_response = client.post(
                    f"/api/v1/projects/{project_data['project']['id']}/adrs",
                    params=adr_data
                )
                assert adr_response.status_code == 201
                results["adrs"].append(adr_response.json())
            
            # Create solution outline
            solution_outline_response = client.post(
                f"/api/v1/projects/{project_data['project']['id']}/solution-outlines",
                params=project_data["solution_outline"]
            )
            assert solution_outline_response.status_code == 201
            results["solution_outline"] = solution_outline_response.json()
            
            return results
        
        @staticmethod
        def verify_project_completeness(client: TestClient, project_id: str) -> Dict[str, Any]:
            """Verify that a project has all expected components."""
            verification = {}
            
            # Verify project exists
            project_response = client.get(f"/api/v1/projects/{project_id}")
            verification["project_exists"] = project_response.status_code == 200
            
            # Verify teams exist
            teams_response = client.get(f"/api/v1/projects/{project_id}/teams")
            verification["teams_exist"] = teams_response.status_code == 200
            verification["teams_count"] = len(teams_response.json().get("data", []))
            
            # Verify ADRs exist
            adrs_response = client.get(f"/api/v1/projects/{project_id}/adrs")
            verification["adrs_exist"] = adrs_response.status_code == 200
            verification["adrs_count"] = len(adrs_response.json().get("data", []))
            
            # Verify solution outline exists
            solution_outline_response = client.get(f"/api/v1/projects/{project_id}/solution-outlines/latest")
            verification["solution_outline_exists"] = solution_outline_response.status_code == 200
            
            return verification
        
        @staticmethod
        def simulate_user_workflow(client: TestClient, workflow_type: str, project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Simulate a complete user workflow."""
            workflow_steps = []
            
            if workflow_type == "project_creation":
                # Step 1: Create project
                step = {"action": "create_project", "status": "started"}
                project_response = client.post("/api/v1/projects", json=project_data["project"])
                step["response_code"] = project_response.status_code
                step["status"] = "completed" if project_response.status_code == 201 else "failed"
                workflow_steps.append(step)
                
                # Step 2: Add teams
                for i, team_data in enumerate(project_data["teams"]):
                    step = {"action": f"create_team_{i+1}", "status": "started"}
                    team_response = client.post(
                        f"/api/v1/projects/{project_data['project']['id']}/teams",
                        json=team_data
                    )
                    step["response_code"] = team_response.status_code
                    step["status"] = "completed" if team_response.status_code == 201 else "failed"
                    workflow_steps.append(step)
                
                # Step 3: Create ADRs
                for i, adr_data in enumerate(project_data["adrs"]):
                    step = {"action": f"create_adr_{i+1}", "status": "started"}
                    adr_response = client.post(
                        f"/api/v1/projects/{project_data['project']['id']}/adrs",
                        params=adr_data
                    )
                    step["response_code"] = adr_response.status_code
                    step["status"] = "completed" if adr_response.status_code == 201 else "failed"
                    workflow_steps.append(step)
                
                # Step 4: Create solution outline
                step = {"action": "create_solution_outline", "status": "started"}
                solution_response = client.post(
                    f"/api/v1/projects/{project_data['project']['id']}/solution-outlines",
                    params=project_data["solution_outline"]
                )
                step["response_code"] = solution_response.status_code
                step["status"] = "completed" if solution_response.status_code == 201 else "failed"
                workflow_steps.append(step)
            
            return workflow_steps
    
    return WorkflowHelpers()

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()