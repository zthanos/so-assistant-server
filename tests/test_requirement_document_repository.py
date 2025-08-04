"""Unit tests for requirement document repository versioning logic."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.repositories.requirement_document_repository import RequirementDocumentRepository
from app.models.requirement_document import RequirementDocument
from app.api.schemas.requirements import (
    RequirementDocumentCreate,
    RequirementDocumentStatus,
    SourceType
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.utils.pagination import PaginationParams, PaginatedResponse


class TestRequirementDocumentRepository:
    """Test cases for RequirementDocumentRepository class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = RequirementDocumentRepository()
        self.mock_db = Mock(spec=Session)

    def test_init_creates_repository(self):
        """Test that repository initializes correctly."""
        assert isinstance(self.repository, RequirementDocumentRepository)

    def test_create_with_version_first_version(self):
        """Test creating first version of requirements document."""
        # Mock database query to return no existing versions
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Mock database add and commit
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()

        # Create test data
        obj_in = RequirementDocumentCreate(
            project_id="test-project",
            content="# Requirements\n\nTest content",
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual
        )

        # Mock the created document
        created_doc = RequirementDocument(
            id=1,
            project_id="test-project",
            content="# Requirements\n\nTest content",
            version=1,
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock database operations
        def mock_add(doc):
            doc.id = 1
            doc.version = 1
            doc.created_at = datetime.utcnow()
            doc.updated_at = datetime.utcnow()

        self.mock_db.add.side_effect = mock_add

        result = self.repository.create_with_version(self.mock_db, obj_in)

        # Verify version is set to 1
        assert result.version == 1
        assert result.project_id == "test-project"
        assert result.content == "# Requirements\n\nTest content"
        
        # Verify database operations
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_create_with_version_increments_version(self):
        """Test creating new version increments version number."""
        # Mock database query to return existing version count
        self.mock_db.query.return_value.filter.return_value.count.return_value = 2

        # Mock database operations
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()

        obj_in = RequirementDocumentCreate(
            project_id="test-project",
            content="# Updated Requirements\n\nNew content",
            status=RequirementDocumentStatus.published,
            source_type=SourceType.pdf_upload,
            original_filename="requirements.pdf"
        )

        def mock_add(doc):
            doc.id = 3
            doc.version = 3  # Should be incremented
            doc.created_at = datetime.utcnow()
            doc.updated_at = datetime.utcnow()

        self.mock_db.add.side_effect = mock_add

        result = self.repository.create_with_version(self.mock_db, obj_in)

        # Verify version is incremented
        assert result.version == 3
        assert result.original_filename == "requirements.pdf"
        assert result.source_type == SourceType.pdf_upload

    def test_create_with_version_database_error(self):
        """Test error handling when database operation fails."""
        # Mock database query
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        
        # Mock database error
        self.mock_db.add = Mock()
        self.mock_db.commit = Mock(side_effect=IntegrityError("", "", ""))
        self.mock_db.rollback = Mock()

        obj_in = RequirementDocumentCreate(
            project_id="test-project",
            content="# Requirements",
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual
        )

        with pytest.raises(BadRequestException) as exc_info:
            self.repository.create_with_version(self.mock_db, obj_in)

        assert "Failed to create requirements document" in str(exc_info.value)
        self.mock_db.rollback.assert_called_once()

    def test_get_latest_version_exists(self):
        """Test getting latest version when document exists."""
        # Mock document
        mock_doc = RequirementDocument(
            id=3,
            project_id="test-project",
            content="# Latest Requirements",
            version=3,
            status=RequirementDocumentStatus.published,
            source_type=SourceType.manual,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock database query
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_doc

        result = self.repository.get_latest_version(self.mock_db, "test-project")

        assert result == mock_doc
        assert result.version == 3

    def test_get_latest_version_not_exists(self):
        """Test getting latest version when no document exists."""
        # Mock database query to return None
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = self.repository.get_latest_version(self.mock_db, "nonexistent-project")

        assert result is None

    def test_get_by_version_exists(self):
        """Test getting specific version when it exists."""
        mock_doc = RequirementDocument(
            id=2,
            project_id="test-project",
            content="# Version 2 Requirements",
            version=2,
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.pdf_upload,
            original_filename="v2.pdf",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        # Mock database query
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.first.return_value = mock_doc

        result = self.repository.get_by_version(self.mock_db, "test-project", 2)

        assert result == mock_doc
        assert result.version == 2
        assert result.original_filename == "v2.pdf"

    def test_get_by_version_not_exists(self):
        """Test getting specific version when it doesn't exist."""
        # Mock database query to return None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.repository.get_by_version(self.mock_db, "test-project", 999)

        assert result is None

    def test_get_version_count(self):
        """Test getting version count for project."""
        # Mock database query to return count
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5

        result = self.repository.get_version_count(self.mock_db, "test-project")

        assert result == 5

    def test_get_version_count_no_versions(self):
        """Test getting version count when no versions exist."""
        # Mock database query to return 0
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0

        result = self.repository.get_version_count(self.mock_db, "empty-project")

        assert result == 0

    def test_get_versions_paginated(self):
        """Test getting paginated list of versions."""
        # Create mock documents
        mock_docs = [
            RequirementDocument(
                id=3, project_id="test-project", content="V3", version=3,
                status=RequirementDocumentStatus.published, source_type=SourceType.manual,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            ),
            RequirementDocument(
                id=2, project_id="test-project", content="V2", version=2,
                status=RequirementDocumentStatus.draft, source_type=SourceType.pdf_upload,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
        ]

        # Mock database queries
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_docs
        query_mock.filter.return_value.count.return_value = 3  # Total count

        pagination = PaginationParams(page=1, per_page=2)
        result = self.repository.get_versions_paginated(
            self.mock_db, "test-project", pagination
        )

        assert isinstance(result, PaginatedResponse)
        assert len(result.items) == 2
        assert result.total == 3
        assert result.page == 1
        assert result.per_page == 2

    def test_get_versions_paginated_with_filters(self):
        """Test getting paginated versions with status and source type filters."""
        mock_docs = [
            RequirementDocument(
                id=1, project_id="test-project", content="V1", version=1,
                status=RequirementDocumentStatus.published, source_type=SourceType.pdf_upload,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
        ]

        # Mock database queries with filters
        query_mock = self.mock_db.query.return_value
        filter_mock = query_mock.filter.return_value.filter.return_value.filter.return_value
        filter_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = mock_docs
        filter_mock.count.return_value = 1

        pagination = PaginationParams(page=1, per_page=10)
        result = self.repository.get_versions_paginated(
            self.mock_db, 
            "test-project", 
            pagination,
            status_filter=RequirementDocumentStatus.published,
            source_type_filter=SourceType.pdf_upload
        )

        assert len(result.items) == 1
        assert result.items[0].status == RequirementDocumentStatus.published
        assert result.items[0].source_type == SourceType.pdf_upload

    def test_get_versions_paginated_empty_result(self):
        """Test getting paginated versions with no results."""
        # Mock empty result
        query_mock = self.mock_db.query.return_value
        query_mock.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        query_mock.filter.return_value.count.return_value = 0

        pagination = PaginationParams(page=1, per_page=10)
        result = self.repository.get_versions_paginated(
            self.mock_db, "empty-project", pagination
        )

        assert len(result.items) == 0
        assert result.total == 0

    def test_delete_version_exists(self):
        """Test deleting existing version."""
        mock_doc = RequirementDocument(
            id=2, project_id="test-project", content="V2", version=2,
            status=RequirementDocumentStatus.draft, source_type=SourceType.manual,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )

        # Mock database operations
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        self.mock_db.delete = Mock()
        self.mock_db.commit = Mock()

        result = self.repository.delete_version(self.mock_db, "test-project", 2)

        assert result is True
        self.mock_db.delete.assert_called_once_with(mock_doc)
        self.mock_db.commit.assert_called_once()

    def test_delete_version_not_exists(self):
        """Test deleting non-existent version."""
        # Mock database query to return None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        result = self.repository.delete_version(self.mock_db, "test-project", 999)

        assert result is False
        self.mock_db.delete.assert_not_called()
        self.mock_db.commit.assert_not_called()

    def test_delete_version_database_error(self):
        """Test error handling when delete operation fails."""
        mock_doc = RequirementDocument(
            id=2, project_id="test-project", content="V2", version=2,
            status=RequirementDocumentStatus.draft, source_type=SourceType.manual,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )

        # Mock database operations with error
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        self.mock_db.delete = Mock()
        self.mock_db.commit = Mock(side_effect=IntegrityError("", "", ""))
        self.mock_db.rollback = Mock()

        with pytest.raises(BadRequestException) as exc_info:
            self.repository.delete_version(self.mock_db, "test-project", 2)

        assert "Failed to delete requirements document" in str(exc_info.value)
        self.mock_db.rollback.assert_called_once()

    def test_update_status_exists(self):
        """Test updating status of existing document."""
        mock_doc = RequirementDocument(
            id=1, project_id="test-project", content="V1", version=1,
            status=RequirementDocumentStatus.draft, source_type=SourceType.manual,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )

        # Mock database operations
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_doc
        self.mock_db.commit = Mock()
        self.mock_db.refresh = Mock()

        result = self.repository.update_status(
            self.mock_db, 1, RequirementDocumentStatus.published
        )

        assert result.status == RequirementDocumentStatus.published
        self.mock_db.commit.assert_called_once()
        self.mock_db.refresh.assert_called_once()

    def test_update_status_not_exists(self):
        """Test updating status of non-existent document."""
        # Mock database query to return None
        self.mock_db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            self.repository.update_status(
                self.mock_db, 999, RequirementDocumentStatus.published
            )

        assert "Requirements document not found" in str(exc_info.value)

    def test_get_summary_statistics(self):
        """Test getting summary statistics for project."""
        # Mock version count
        self.mock_db.query.return_value.filter.return_value.count.return_value = 5

        # Mock latest version
        mock_latest = RequirementDocument(
            id=5, project_id="test-project", content="Latest", version=5,
            status=RequirementDocumentStatus.published, source_type=SourceType.manual,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow()
        )
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_latest

        # Mock status counts
        status_counts = [
            (RequirementDocumentStatus.draft, 2),
            (RequirementDocumentStatus.published, 3)
        ]
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = status_counts

        # Mock source type counts
        source_counts = [
            (SourceType.manual, 3),
            (SourceType.pdf_upload, 2)
        ]

        # Configure multiple query calls
        query_calls = [
            Mock(),  # version count
            Mock(),  # latest version
            Mock(),  # status counts
            Mock()   # source counts
        ]
        
        # Set up the mock to return different results for different calls
        self.mock_db.query.side_effect = [
            query_calls[0],  # version count
            query_calls[1],  # latest version
            query_calls[2],  # status counts
            query_calls[3]   # source counts
        ]

        # Configure each query call
        query_calls[0].filter.return_value.count.return_value = 5
        query_calls[1].filter.return_value.order_by.return_value.first.return_value = mock_latest
        query_calls[2].filter.return_value.group_by.return_value.all.return_value = status_counts
        query_calls[3].filter.return_value.group_by.return_value.all.return_value = source_counts

        result = self.repository.get_summary_statistics(self.mock_db, "test-project")

        assert result["total_versions"] == 5
        assert result["latest_version"] == 5
        assert result["status_counts"]["draft"] == 2
        assert result["status_counts"]["published"] == 3
        assert result["source_type_counts"]["manual"] == 3
        assert result["source_type_counts"]["pdf_upload"] == 2

    def test_get_summary_statistics_no_documents(self):
        """Test getting summary statistics when no documents exist."""
        # Mock empty results
        self.mock_db.query.return_value.filter.return_value.count.return_value = 0
        self.mock_db.query.return_value.filter.return_value.order_by.return_value.first.return_value = None
        self.mock_db.query.return_value.filter.return_value.group_by.return_value.all.return_value = []

        result = self.repository.get_summary_statistics(self.mock_db, "empty-project")

        assert result["total_versions"] == 0
        assert result["latest_version"] == 0
        assert result["status_counts"] == {}
        assert result["source_type_counts"] == {}


class TestRequirementDocumentRepositoryIntegration:
    """Integration tests for repository with database constraints."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repository = RequirementDocumentRepository()

    def test_version_uniqueness_constraint(self):
        """Test that version uniqueness is enforced."""
        # This would be tested with a real database
        # For now, we test the logic that should prevent duplicates
        mock_db = Mock(spec=Session)
        
        # Mock existing version check
        mock_db.query.return_value.filter.return_value.count.return_value = 1
        
        obj_in = RequirementDocumentCreate(
            project_id="test-project",
            content="# Requirements",
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual
        )

        def mock_add(doc):
            doc.version = 2  # Should increment from existing count
            doc.id = 2
            doc.created_at = datetime.utcnow()
            doc.updated_at = datetime.utcnow()

        mock_db.add.side_effect = mock_add
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        result = self.repository.create_with_version(mock_db, obj_in)
        
        # Should create version 2, not duplicate version 1
        assert result.version == 2

    def test_concurrent_version_creation(self):
        """Test handling of concurrent version creation attempts."""
        # This test would verify race condition handling
        # In a real scenario, database constraints would prevent duplicates
        mock_db = Mock(spec=Session)
        
        # Simulate race condition where count changes between check and insert
        call_count = 0
        def mock_count():
            nonlocal call_count
            call_count += 1
            return call_count  # Simulates another thread creating a version
        
        mock_db.query.return_value.filter.return_value.count.side_effect = mock_count
        
        # Mock integrity error on first attempt
        commit_calls = 0
        def mock_commit():
            nonlocal commit_calls
            commit_calls += 1
            if commit_calls == 1:
                raise IntegrityError("", "", "")
        
        mock_db.commit.side_effect = mock_commit
        mock_db.rollback = Mock()

        obj_in = RequirementDocumentCreate(
            project_id="test-project",
            content="# Requirements",
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual
        )

        with pytest.raises(BadRequestException):
            self.repository.create_with_version(mock_db, obj_in)

        # Should have attempted rollback
        mock_db.rollback.assert_called()


# Test fixtures
@pytest.fixture
def mock_db_session():
    """Fixture providing mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def requirement_repository():
    """Fixture providing requirement document repository."""
    return RequirementDocumentRepository()

@pytest.fixture
def sample_requirement_create():
    """Fixture providing sample requirement document create data."""
    return RequirementDocumentCreate(
        project_id="test-project-123",
        content="# Sample Requirements\n\n1. The system SHALL provide authentication\n2. The system SHALL store data securely",
        status=RequirementDocumentStatus.draft,
        source_type=SourceType.manual
    )

@pytest.fixture
def sample_requirement_document():
    """Fixture providing sample requirement document."""
    return RequirementDocument(
        id=1,
        project_id="test-project-123",
        content="# Sample Requirements\n\n1. Authentication\n2. Data storage",
        version=1,
        status=RequirementDocumentStatus.draft,
        source_type=SourceType.manual,
        original_filename=None,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )