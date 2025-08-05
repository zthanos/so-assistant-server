"""Unit tests for RequirementSuggestionService."""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session

from app.services.requirement_suggestion_service import RequirementSuggestionService
from app.services.llm.streaming import LLMStreamingService
from app.repositories.requirement_document_repository import RequirementDocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.core.events import SSEManager
from app.domain.models.requirements import RequirementDocument, RequirementDocumentStatus, SourceType
from app.domain.models.projects import Project, ProjectState
from app.api.schemas.requirements import RequirementSuggestion, RequirementItemPriority
from app.core.exceptions import NotFoundException, BadRequestException, LLMException


@pytest.fixture
def mock_llm_streaming_service():
    """Create a mock LLM streaming service."""
    return MagicMock(spec=LLMStreamingService)


@pytest.fixture
def mock_requirement_document_repository():
    """Create a mock requirement document repository."""
    return MagicMock(spec=RequirementDocumentRepository)


@pytest.fixture
def mock_project_repository():
    """Create a mock project repository."""
    return MagicMock(spec=ProjectRepository)


@pytest.fixture
def mock_sse_manager():
    """Create a mock SSE manager."""
    return MagicMock(spec=SSEManager)


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def service(
    mock_llm_streaming_service,
    mock_requirement_document_repository,
    mock_project_repository,
    mock_sse_manager
):
    """Create a RequirementSuggestionService instance with mock dependencies."""
    return RequirementSuggestionService(
        mock_llm_streaming_service,
        mock_requirement_document_repository,
        mock_project_repository,
        mock_sse_manager
    )


@pytest.fixture
def sample_project():
    """Create a sample project."""
    return Project(
        id="test-project-1",
        name="Test Project",
        description="A test project",
        state=ProjectState.active
    )


@pytest.fixture
def sample_requirements_document():
    """Create a sample requirements document."""
    return RequirementDocument(
        id=1,
        project_id="test-project-1",
        content="# Requirements\n\n## User Authentication\nThe system shall provide user authentication.",
        version=1,
        status=RequirementDocumentStatus.published,
        source_type=SourceType.manual
    )


@pytest.fixture
def sample_suggestion_response():
    """Create a sample LLM suggestion response."""
    return json.dumps([
        {
            "title": "Password Complexity Requirements",
            "description": "The system shall enforce password complexity rules including minimum length, special characters, and mixed case.",
            "priority": "high",
            "rationale": "Strong password requirements are essential for security and complement the basic authentication requirement."
        },
        {
            "title": "Session Timeout",
            "description": "The system shall automatically log out users after 30 minutes of inactivity.",
            "priority": "medium",
            "rationale": "Session timeout prevents unauthorized access when users leave their sessions unattended."
        }
    ])


class TestRequirementSuggestionService:
    """Test RequirementSuggestionService class."""
    
    def test_init(
        self,
        mock_llm_streaming_service,
        mock_requirement_document_repository,
        mock_project_repository,
        mock_sse_manager
    ):
        """Test service initialization."""
        service = RequirementSuggestionService(
            mock_llm_streaming_service,
            mock_requirement_document_repository,
            mock_project_repository,
            mock_sse_manager
        )
        
        assert service.llm_streaming_service == mock_llm_streaming_service
        assert service.requirement_document_repository == mock_requirement_document_repository
        assert service.project_repository == mock_project_repository
        assert service.sse_manager == mock_sse_manager
    
    @pytest.mark.asyncio
    async def test_stream_requirement_suggestions_success(
        self,
        service,
        mock_db_session,
        mock_project_repository,
        mock_requirement_document_repository,
        mock_llm_streaming_service,
        mock_sse_manager,
        sample_project,
        sample_requirements_document,
        sample_suggestion_response
    ):
        """Test successful requirement suggestions streaming."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_document_repository.get_latest_version.return_value = sample_requirements_document
        mock_sse_manager.send_event = AsyncMock()
        
        # Mock LLM streaming response
        async def mock_streaming_response(*args, **kwargs):
            yield ("llm.start", {"message": "Starting"})
            yield ("llm.chunk", {"content": sample_suggestion_response})
            yield ("llm.complete", {"message": "Complete"})
        
        mock_llm_streaming_service.create_streaming_response = mock_streaming_response
        
        # Execute
        await service.stream_requirement_suggestions(
            mock_db_session, "client-1", "test-project-1", 10
        )
        
        # Verify
        mock_project_repository.get.assert_called_once_with(mock_db_session, "test-project-1")
        mock_requirement_document_repository.get_latest_version.assert_called_once_with(
            mock_db_session, "test-project-1"
        )
        
        # Verify SSE events were sent
        assert mock_sse_manager.send_event.call_count >= 3  # start, items, complete
    
    @pytest.mark.asyncio
    async def test_stream_requirement_suggestions_project_not_found(
        self,
        service,
        mock_db_session,
        mock_project_repository
    ):
        """Test streaming when project doesn't exist."""
        # Setup mock
        mock_project_repository.get.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await service.stream_requirement_suggestions(
                mock_db_session, "client-1", "non-existent-project", 10
            )
        
        assert "Project with id non-existent-project not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_requirement_suggestions_no_requirements_document(
        self,
        service,
        mock_db_session,
        mock_project_repository,
        mock_requirement_document_repository,
        sample_project
    ):
        """Test streaming when no requirements document exists."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_document_repository.get_latest_version.return_value = None
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            await service.stream_requirement_suggestions(
                mock_db_session, "client-1", "test-project-1", 10
            )
        
        assert "No requirements document found for project test-project-1" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_requirement_suggestions_invalid_max_suggestions(
        self,
        service,
        mock_db_session
    ):
        """Test streaming with invalid max_suggestions parameter."""
        # Test too low
        with pytest.raises(BadRequestException) as exc_info:
            await service.stream_requirement_suggestions(
                mock_db_session, "client-1", "test-project-1", 0
            )
        assert "max_suggestions must be between 1 and 50" in str(exc_info.value)
        
        # Test too high
        with pytest.raises(BadRequestException) as exc_info:
            await service.stream_requirement_suggestions(
                mock_db_session, "client-1", "test-project-1", 51
            )
        assert "max_suggestions must be between 1 and 50" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_stream_requirement_suggestions_llm_error(
        self,
        service,
        mock_db_session,
        mock_project_repository,
        mock_requirement_document_repository,
        mock_llm_streaming_service,
        mock_sse_manager,
        sample_project,
        sample_requirements_document
    ):
        """Test streaming when LLM returns an error."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_document_repository.get_latest_version.return_value = sample_requirements_document
        mock_sse_manager.send_event = AsyncMock()
        
        # Mock LLM streaming response with error
        async def mock_streaming_response(*args, **kwargs):
            yield ("llm.start", {"message": "Starting"})
            yield ("llm.error", {"message": "LLM processing failed", "error_type": "llm_error"})
        
        mock_llm_streaming_service.create_streaming_response = mock_streaming_response
        
        # Execute and verify exception
        with pytest.raises(LLMException) as exc_info:
            await service.stream_requirement_suggestions(
                mock_db_session, "client-1", "test-project-1", 10
            )
        
        assert "LLM error: LLM processing failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_generate_suggestions_batch_success(
        self,
        service,
        mock_db_session,
        mock_project_repository,
        mock_requirement_document_repository,
        mock_llm_streaming_service,
        sample_project,
        sample_requirements_document,
        sample_suggestion_response
    ):
        """Test successful batch suggestion generation."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_document_repository.get_latest_version.return_value = sample_requirements_document
        
        # Mock LLM streaming response
        async def mock_streaming_response(*args, **kwargs):
            yield ("llm.chunk", {"content": sample_suggestion_response})
            yield ("llm.complete", {"message": "Complete"})
        
        mock_llm_streaming_service.create_streaming_response = mock_streaming_response
        
        # Execute
        result = await service.generate_suggestions_batch(
            mock_db_session, "test-project-1", 10
        )
        
        # Verify
        assert len(result) == 2
        assert isinstance(result[0], RequirementSuggestion)
        assert result[0].title == "Password Complexity Requirements"
        assert result[0].priority == RequirementItemPriority.high
        assert result[1].title == "Session Timeout"
        assert result[1].priority == RequirementItemPriority.medium


class TestSuggestionParsing:
    """Test suggestion parsing methods."""
    
    def test_parse_suggestion_response_valid_json(self, service):
        """Test parsing valid JSON response."""
        response = json.dumps([
            {
                "title": "Test Requirement",
                "description": "This is a test requirement",
                "priority": "high",
                "rationale": "This is needed for testing"
            }
        ])
        
        result = service._parse_suggestion_response(response)
        
        assert len(result) == 1
        assert result[0].title == "Test Requirement"
        assert result[0].priority == RequirementItemPriority.high
    
    def test_parse_suggestion_response_invalid_json(self, service):
        """Test parsing invalid JSON response."""
        response = "This is not valid JSON"
        
        result = service._parse_suggestion_response(response)
        
        assert len(result) == 0
    
    def test_parse_suggestion_response_with_markdown(self, service):
        """Test parsing response with markdown formatting."""
        response = f"""Here are the suggestions:

```json
{json.dumps([
    {
        "title": "Test Requirement",
        "description": "This is a test requirement",
        "priority": "medium",
        "rationale": "This is needed for testing"
    }
])}
```

That's all!"""
        
        result = service._parse_suggestion_response(response)
        
        assert len(result) == 1
        assert result[0].title == "Test Requirement"
    
    def test_is_complete_suggestion_valid(self, service):
        """Test checking complete suggestion."""
        item = {
            "title": "Test",
            "description": "Description",
            "priority": "high",
            "rationale": "Rationale"
        }
        
        assert service._is_complete_suggestion(item) is True
    
    def test_is_complete_suggestion_missing_field(self, service):
        """Test checking incomplete suggestion."""
        item = {
            "title": "Test",
            "description": "Description",
            "priority": "high"
            # Missing rationale
        }
        
        assert service._is_complete_suggestion(item) is False
    
    def test_create_suggestion_from_dict_valid(self, service):
        """Test creating suggestion from valid dictionary."""
        item = {
            "title": "Test Requirement",
            "description": "This is a test requirement",
            "priority": "critical",
            "rationale": "This is needed for testing"
        }
        
        result = service._create_suggestion_from_dict(item)
        
        assert result is not None
        assert result.title == "Test Requirement"
        assert result.priority == RequirementItemPriority.critical
    
    def test_create_suggestion_from_dict_invalid_priority(self, service):
        """Test creating suggestion with invalid priority."""
        item = {
            "title": "Test Requirement",
            "description": "This is a test requirement",
            "priority": "invalid_priority",
            "rationale": "This is needed for testing"
        }
        
        result = service._create_suggestion_from_dict(item)
        
        assert result is not None
        assert result.priority == RequirementItemPriority.medium  # Default fallback
    
    def test_create_suggestion_from_dict_incomplete(self, service):
        """Test creating suggestion from incomplete dictionary."""
        item = {
            "title": "Test Requirement",
            "description": "This is a test requirement"
            # Missing priority and rationale
        }
        
        result = service._create_suggestion_from_dict(item)
        
        assert result is None


class TestPromptBuilding:
    """Test prompt building methods."""
    
    def test_get_system_prompt(self, service):
        """Test system prompt generation."""
        result = service._get_system_prompt()
        
        assert "business analyst" in result.lower()
        assert "requirements" in result.lower()
        assert "functional" in result.lower()
        assert "non-functional" in result.lower()
    
    def test_build_suggestion_prompt(self, service):
        """Test suggestion prompt building."""
        requirements_content = "# Requirements\n\nUser authentication is required."
        max_suggestions = 5
        
        result = service._build_suggestion_prompt(requirements_content, max_suggestions)
        
        assert requirements_content in result
        assert str(max_suggestions) in result
        assert "JSON format" in result
        assert "title" in result
        assert "description" in result
        assert "priority" in result
        assert "rationale" in result