"""Integration test configuration and fixtures.

This module provides common fixtures and configuration for integration tests.
"""
import pytest
import asyncio
from typing import Generator, AsyncGenerator
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

@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "id": "test-project-1",
        "name": "Test Project",
        "description": "A test project for integration testing",
        "code": "TP001",
        "state": "active"
    }

@pytest.fixture
def sample_team_data():
    """Sample team data for testing."""
    return {
        "name": "Test Team",
        "members": "John Doe, Jane Smith"
    }

@pytest.fixture
def sample_adr_data():
    """Sample ADR data for testing."""
    return {
        "title": "Test ADR",
        "content": "This is a test Architecture Decision Record"
    }

@pytest.fixture
def sample_solution_outline_data():
    """Sample solution outline data for testing."""
    return {
        "content": "This is a test solution outline content",
        "status": "draft"
    }

# Event loop fixture for async tests
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()