"""Test configuration and fixtures.

This module provides common test configuration and fixtures for the test suite.
"""
import pytest
import sys
import os
from unittest.mock import MagicMock

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_db_session():
    """Provide a mock database session."""
    return MagicMock()

@pytest.fixture
def mock_repository():
    """Provide a mock repository."""
    return MagicMock()

@pytest.fixture
def mock_service():
    """Provide a mock service."""
    return MagicMock()

# Configure pytest to ignore warnings from dependencies
def pytest_configure(config):
    """Configure pytest settings."""
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)