"""Unit tests for requirement document service layer business logic."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from fastapi import UploadFile
from sqlalchemy.orm import Session
from datetime import datetime
import io

from app.services.requirement_document_service import RequirementDocumentService
from app.repositories.requirement_document_repository import RequirementDocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.services.pdf_processor import PDFProcessor
from app.services.requirements_pdf_converter import RequirementsPDFConverter
from app.models.requirement_document import RequirementDocument
from app.models.project import Project
from app.api.schemas.requirements import (
    RequirementDocumentStatus,
    SourceType
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.exceptions.pdf_exceptions import (
    InvalidPDFError,
    PDFTooLargeError,
    TextExtractionError,
    LLMConversionError
)
from app.utils.pagination import PaginationParams, PaginatedResponse


class TestRequirementDocumentService:
    """Test cases for RequirementDocumentService class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.mock_requirement_repo = Mock(spec=RequirementDocumentRepository)
        self.mock_project_repo = Mock(spec=ProjectRepository)
        self.mock_pdf_processor = Mock(spec=PDFProcessor)
        self.mock_pdf_converter = Mock(spec=RequirementsPDFConverter)

        # Create service with mocked dependencies
        self.service = RequirementDocumentService(self.mock_db)
        self.service.requirement_repository = self.mock_requirement_repo
        self.service.project_repository = self.mock_project_repo
        self.service.pdf_processor = self.mock_pdf_processor
        self.service.pdf_converter = self.mock_pdf_converter

    def test_init_creates_service_with_dependencies(self):
        """Test that service initializes with correct dependencies."""
        db = Mock(spec=Session)
        service = RequirementDocumentService(db)
        
        assert service.db == db
        assert isinstance(service.requirement_repository, RequirementDocumentRepository)
        assert isinstance(service.project_repository, ProjectRepository)
        assert isinstance(service.pdf_processor, PDFProcessor)
        assert isinstance(service.pdf_converter, RequirementsPDFConverter)

    def test_upsert_requirements_project_not_found(self):
        """Test upsert fails when project doesn't exist."""
        # Mock project repository to return None
        self.mock_project_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            self.service.upsert_requirements(
                project_id="nonexistent-project",
                content="# Requirements",
                status=RequirementDocumentStatus.draft,
                source_type=SourceType.manual
            )

        assert "Project not found" in str(exc_info.value)
        self.mock_project_repo.get_by_id.assert_called_once_with(
            self.mock_db, "nonexistent-project"
        )

    def test_upsert_requirements_empty_content(self):
        """Test upsert fails with empty content."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        with pytest.raises(BadRequestException) as exc_info:
            self.service.upsert_requirements(
                project_id="test-project",
                content="",
                status=RequirementDocumentStatus.draft,
                source_type=SourceType.manual
            )

        assert "Content cannot be empty" in str(exc_info.value)

    def test_upsert_requirements_success_new_document(self):
        """Test successful upsert for new requirements document."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock created document
        mock_document = RequirementDocument(
            id=1,
            project_id="test-project",
            content="# Requirements\n\nTest content",
            version=1,
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_requirement_repo.create_with_version.return_value = mock_document

        result = self.service.upsert_requirements(
            project_id="test-project",
            content="# Requirements\n\nTest content",
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.manual
        )

        assert result == mock_document
        assert result.version == 1
        self.mock_requirement_repo.create_with_version.assert_called_once()

    def test_upsert_requirements_success_with_filename(self):
        """Test successful upsert with original filename."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock created document
        mock_document = RequirementDocument(
            id=2,
            project_id="test-project",
            content="# PDF Requirements",
            version=2,
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.pdf_upload,
            original_filename="requirements.pdf",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_requirement_repo.create_with_version.return_value = mock_document

        result = self.service.upsert_requirements(
            project_id="test-project",
            content="# PDF Requirements",
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.pdf_upload,
            original_filename="requirements.pdf"
        )

        assert result.original_filename == "requirements.pdf"
        assert result.source_type == SourceType.pdf_upload

    def test_get_latest_requirements_exists(self):
        """Test getting latest requirements when document exists."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock latest document
        mock_document = RequirementDocument(
            id=3,
            project_id="test-project",
            content="# Latest Requirements",
            version=3,
            status=RequirementDocumentStatus.published,
            source_type=SourceType.manual,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_requirement_repo.get_latest_version.return_value = mock_document

        result = self.service.get_latest_requirements("test-project")

        assert result == mock_document
        assert result.version == 3

    def test_get_latest_requirements_empty_fallback(self):
        """Test getting latest requirements returns empty document when none exists."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock no existing document
        self.mock_requirement_repo.get_latest_version.return_value = None

        result = self.service.get_latest_requirements("test-project")

        # Should return empty document
        assert result.project_id == "test-project"
        assert result.content == ""
        assert result.version == 0
        assert result.status == RequirementDocumentStatus.draft
        assert result.source_type == SourceType.manual

    def test_get_latest_requirements_project_not_found(self):
        """Test getting latest requirements fails when project doesn't exist."""
        # Mock project doesn't exist
        self.mock_project_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            self.service.get_latest_requirements("nonexistent-project")

        assert "Project not found" in str(exc_info.value)

    def test_get_requirements_by_version_success(self):
        """Test getting specific version successfully."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock specific version
        mock_document = RequirementDocument(
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
        self.mock_requirement_repo.get_by_version.return_value = mock_document

        result = self.service.get_requirements_by_version("test-project", 2)

        assert result == mock_document
        assert result.version == 2

    def test_get_requirements_by_version_not_found(self):
        """Test getting specific version that doesn't exist."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock version doesn't exist
        self.mock_requirement_repo.get_by_version.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            self.service.get_requirements_by_version("test-project", 999)

        assert "Requirements document version 999 not found" in str(exc_info.value)

    def test_get_requirements_versions_success(self):
        """Test getting paginated versions successfully."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock paginated result
        mock_documents = [
            RequirementDocument(
                id=2, project_id="test-project", content="V2", version=2,
                status=RequirementDocumentStatus.published, source_type=SourceType.manual,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            ),
            RequirementDocument(
                id=1, project_id="test-project", content="V1", version=1,
                status=RequirementDocumentStatus.draft, source_type=SourceType.pdf_upload,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
        ]

        mock_paginated_result = PaginatedResponse(
            items=mock_documents,
            total=2,
            page=1,
            per_page=10,
            pages=1,
            has_next=False,
            has_prev=False
        )
        self.mock_requirement_repo.get_versions_paginated.return_value = mock_paginated_result

        pagination = PaginationParams(page=1, per_page=10)
        result = self.service.get_requirements_versions(
            project_id="test-project",
            pagination=pagination,
            status_filter=None,
            source_type_filter=None
        )

        assert result == mock_paginated_result
        assert len(result.items) == 2

    @pytest.mark.asyncio
    async def test_process_pdf_upload_success(self):
        """Test successful PDF upload processing."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Create mock file
        file_content = b"fake pdf content"
        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "requirements.pdf"
        mock_file.size = 1024
        mock_file.content_type = "application/pdf"

        # Mock PDF processing
        extracted_text = "Requirements from PDF:\n1. Authentication\n2. Data storage"
        self.mock_pdf_processor.process_pdf_file = AsyncMock(return_value=extracted_text)

        # Mock LLM conversion
        converted_markdown = """# Requirements Document

*Converted from: requirements.pdf*

## Functional Requirements

1. The system SHALL provide authentication
2. The system SHALL provide data storage
"""
        self.mock_pdf_converter.convert_pdf_text_to_markdown = AsyncMock(
            return_value=converted_markdown
        )

        # Mock document creation
        mock_document = RequirementDocument(
            id=1,
            project_id="test-project",
            content=converted_markdown,
            version=1,
            status=RequirementDocumentStatus.draft,
            source_type=SourceType.pdf_upload,
            original_filename="requirements.pdf",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_requirement_repo.create_with_version.return_value = mock_document

        result = await self.service.process_pdf_upload(
            project_id="test-project",
            file=mock_file,
            status=RequirementDocumentStatus.draft
        )

        assert result == mock_document
        assert result.original_filename == "requirements.pdf"
        assert result.source_type == SourceType.pdf_upload

        # Verify all steps were called
        self.mock_pdf_processor.process_pdf_file.assert_called_once_with(mock_file)
        self.mock_pdf_converter.convert_pdf_text_to_markdown.assert_called_once_with(
            extracted_text, "requirements.pdf"
        )

    @pytest.mark.asyncio
    async def test_process_pdf_upload_project_not_found(self):
        """Test PDF upload fails when project doesn't exist."""
        # Mock project doesn't exist
        self.mock_project_repo.get_by_id.return_value = None

        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "requirements.pdf"

        with pytest.raises(NotFoundException) as exc_info:
            await self.service.process_pdf_upload(
                project_id="nonexistent-project",
                file=mock_file,
                status=RequirementDocumentStatus.draft
            )

        assert "Project not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_process_pdf_upload_invalid_pdf(self):
        """Test PDF upload fails with invalid PDF file."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "invalid.txt"

        # Mock PDF processing failure
        self.mock_pdf_processor.process_pdf_file = AsyncMock(
            side_effect=InvalidPDFError("Invalid file type")
        )

        with pytest.raises(InvalidPDFError):
            await self.service.process_pdf_upload(
                project_id="test-project",
                file=mock_file,
                status=RequirementDocumentStatus.draft
            )

    @pytest.mark.asyncio
    async def test_process_pdf_upload_text_extraction_error(self):
        """Test PDF upload handles text extraction errors."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "corrupted.pdf"

        # Mock text extraction failure
        self.mock_pdf_processor.process_pdf_file = AsyncMock(
            side_effect=TextExtractionError("Failed to extract text")
        )

        with pytest.raises(TextExtractionError):
            await self.service.process_pdf_upload(
                project_id="test-project",
                file=mock_file,
                status=RequirementDocumentStatus.draft
            )

    @pytest.mark.asyncio
    async def test_process_pdf_upload_llm_conversion_error(self):
        """Test PDF upload handles LLM conversion errors."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        mock_file = Mock(spec=UploadFile)
        mock_file.filename = "requirements.pdf"

        # Mock successful PDF processing
        extracted_text = "Requirements text"
        self.mock_pdf_processor.process_pdf_file = AsyncMock(return_value=extracted_text)

        # Mock LLM conversion failure
        self.mock_pdf_converter.convert_pdf_text_to_markdown = AsyncMock(
            side_effect=LLMConversionError("LLM service unavailable")
        )

        with pytest.raises(LLMConversionError):
            await self.service.process_pdf_upload(
                project_id="test-project",
                file=mock_file,
                status=RequirementDocumentStatus.draft
            )

    def test_update_requirements_status_success(self):
        """Test successful status update."""
        mock_document = RequirementDocument(
            id=1,
            project_id="test-project",
            content="# Requirements",
            version=1,
            status=RequirementDocumentStatus.published,  # Updated status
            source_type=SourceType.manual,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.mock_requirement_repo.update_status.return_value = mock_document

        result = self.service.update_requirements_status(
            document_id=1,
            new_status=RequirementDocumentStatus.published
        )

        assert result == mock_document
        assert result.status == RequirementDocumentStatus.published

    def test_update_requirements_status_not_found(self):
        """Test status update fails when document doesn't exist."""
        self.mock_requirement_repo.update_status.side_effect = NotFoundException(
            "Requirements document not found"
        )

        with pytest.raises(NotFoundException):
            self.service.update_requirements_status(
                document_id=999,
                new_status=RequirementDocumentStatus.published
            )

    def test_delete_requirements_version_success(self):
        """Test successful version deletion."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock successful deletion
        self.mock_requirement_repo.delete_version.return_value = True

        result = self.service.delete_requirements_version("test-project", 2)

        assert result is True
        self.mock_requirement_repo.delete_version.assert_called_once_with(
            self.mock_db, "test-project", 2
        )

    def test_delete_requirements_version_not_found(self):
        """Test version deletion when version doesn't exist."""
        # Mock project exists
        mock_project = Project(id="test-project", name="Test Project")
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock version not found
        self.mock_requirement_repo.delete_version.return_value = False

        result = self.service.delete_requirements_version("test-project", 999)

        assert result is False

    def test_get_requirements_summary_success(self):
        """Test getting requirements summary successfully."""
        # Mock project exists
        mock_project = Project(
            id="test-project", 
            name="Test Project",
            description="Test project description"
        )
        self.mock_project_repo.get_by_id.return_value = mock_project

        # Mock summary statistics
        mock_stats = {
            "total_versions": 3,
            "latest_version": 3,
            "status_counts": {
                "draft": 1,
                "published": 2
            },
            "source_type_counts": {
                "manual": 2,
                "pdf_upload": 1
            }
        }
        self.mock_requirement_repo.get_summary_statistics.return_value = mock_stats

        result = self.service.get_requirements_summary("test-project")

        # Should include project info and statistics
        assert result["total_versions"] == 3
        assert result["latest_version"] == 3
        assert result["status_counts"]["draft"] == 1
        assert result["status_counts"]["published"] == 2
        assert result["project"]["id"] == "test-project"
        assert result["project"]["name"] == "Test Project"

    def test_get_requirements_summary_project_not_found(self):
        """Test getting summary fails when project doesn't exist."""
        # Mock project doesn't exist
        self.mock_project_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundException) as exc_info:
            self.service.get_requirements_summary("nonexistent-project")

        assert "Project not found" in str(exc_info.value)

    def test_validate_content_empty(self):
        """Test content validation fails for empty content."""
        with pytest.raises(BadRequestException) as exc_info:
            self.service._validate_content("")

        assert "Content cannot be empty" in str(exc_info.value)

    def test_validate_content_whitespace_only(self):
        """Test content validation fails for whitespace-only content."""
        with pytest.raises(BadRequestException) as exc_info:
            self.service._validate_content("   \n  \n  ")

        assert "Content cannot be empty" in str(exc_info.value)

    def test_validate_content_too_long(self):
        """Test content validation fails for overly long content."""
        long_content = "x" * (100000 + 1)  # Over 100KB limit

        with pytest.raises(BadRequestException) as exc_info:
            self.service._validate_content(long_content)

        assert "Content too large" in str(exc_info.value)

    def test_validate_content_valid(self):
        """Test content validation passes for valid content."""
        valid_content = "# Requirements\n\n1. Valid requirement\n2. Another requirement"
        
        # Should not raise exception
        self.service._validate_content(valid_content)

    def test_create_empty_document(self):
        """Test creation of empty requirements document."""
        result = self.service._create_empty_document("test-project")

        assert result.project_id == "test-project"
        assert result.content == ""
        assert result.version == 0
        assert result.status == RequirementDocumentStatus.draft
        assert result.source_type == SourceType.manual
        assert result.original_filename is None


class TestRequirementDocumentServiceIntegration:
    """Integration tests for service with real dependencies."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.service = RequirementDocumentService(self.mock_db)

    @pytest.mark.asyncio
    async def test_complete_pdf_workflow(self):
        """Test complete PDF upload to requirements workflow."""
        # This would test the full integration with real components
        # For now, we test the workflow logic with mocked components
        
        # Mock all dependencies
        with patch.object(self.service, 'project_repository') as mock_proj_repo, \
             patch.object(self.service, 'pdf_processor') as mock_pdf_proc, \
             patch.object(self.service, 'pdf_converter') as mock_pdf_conv, \
             patch.object(self.service, 'requirement_repository') as mock_req_repo:

            # Setup mocks
            mock_project = Project(id="test-project", name="Test Project")
            mock_proj_repo.get_by_id.return_value = mock_project

            mock_file = Mock(spec=UploadFile)
            mock_file.filename = "test.pdf"

            extracted_text = "PDF requirements content"
            mock_pdf_proc.process_pdf_file = AsyncMock(return_value=extracted_text)

            converted_markdown = "# Requirements\n\nConverted content"
            mock_pdf_conv.convert_pdf_text_to_markdown = AsyncMock(
                return_value=converted_markdown
            )

            mock_document = RequirementDocument(
                id=1, project_id="test-project", content=converted_markdown,
                version=1, status=RequirementDocumentStatus.draft,
                source_type=SourceType.pdf_upload, original_filename="test.pdf",
                created_at=datetime.utcnow(), updated_at=datetime.utcnow()
            )
            mock_req_repo.create_with_version.return_value = mock_document

            # Execute workflow
            result = await self.service.process_pdf_upload(
                project_id="test-project",
                file=mock_file,
                status=RequirementDocumentStatus.draft
            )

            # Verify complete workflow
            assert result.original_filename == "test.pdf"
            assert result.source_type == SourceType.pdf_upload
            assert result.content == converted_markdown

            # Verify all steps were executed
            mock_pdf_proc.process_pdf_file.assert_called_once()
            mock_pdf_conv.convert_pdf_text_to_markdown.assert_called_once()
            mock_req_repo.create_with_version.assert_called_once()


# Test fixtures
@pytest.fixture
def mock_db_session():
    """Fixture providing mock database session."""
    return Mock(spec=Session)

@pytest.fixture
def requirement_service(mock_db_session):
    """Fixture providing requirement document service."""
    return RequirementDocumentService(mock_db_session)

@pytest.fixture
def mock_upload_file():
    """Fixture providing mock upload file."""
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test_requirements.pdf"
    mock_file.size = 1024 * 1024  # 1MB
    mock_file.content_type = "application/pdf"
    return mock_file

@pytest.fixture
def sample_project():
    """Fixture providing sample project."""
    return Project(
        id="test-project-123",
        name="Test Project",
        description="A test project for requirements"
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