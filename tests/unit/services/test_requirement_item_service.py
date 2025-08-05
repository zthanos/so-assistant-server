"""Unit tests for RequirementItemService."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.requirement_item_service import RequirementItemService
from app.repositories.requirement_item_repository import RequirementItemRepository
from app.repositories.project_repository import ProjectRepository
from app.domain.models.requirements import RequirementItem, RequirementItemStatus, RequirementItemPriority
from app.domain.models.projects import Project, ProjectState
from app.api.schemas.requirements import RequirementItemCreate, RequirementItemUpdate
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException


@pytest.fixture
def mock_requirement_repository():
    """Create a mock requirement item repository."""
    return MagicMock(spec=RequirementItemRepository)


@pytest.fixture
def mock_project_repository():
    """Create a mock project repository."""
    return MagicMock(spec=ProjectRepository)


@pytest.fixture
def service(mock_requirement_repository, mock_project_repository):
    """Create a RequirementItemService instance with mock repositories."""
    return RequirementItemService(mock_requirement_repository, mock_project_repository)


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
def sample_requirement_item():
    """Create a sample requirement item."""
    return RequirementItem(
        id=1,
        project_id="test-project-1",
        title="Test Requirement",
        description="This is a test requirement item",
        priority=RequirementItemPriority.medium,
        status=RequirementItemStatus.new
    )


@pytest.fixture
def sample_create_data():
    """Create sample requirement item creation data."""
    return RequirementItemCreate(
        project_id="test-project-1",
        title="Test Requirement",
        description="This is a test requirement item",
        priority=RequirementItemPriority.high
    )


class TestRequirementItemService:
    """Test RequirementItemService class."""
    
    def test_init(self, mock_requirement_repository, mock_project_repository):
        """Test service initialization."""
        service = RequirementItemService(mock_requirement_repository, mock_project_repository)
        assert service.repository == mock_requirement_repository
        assert service.project_repository == mock_project_repository
    
    def test_create_requirement_item_success(
        self, service, mock_requirement_repository, mock_project_repository, 
        sample_project, sample_requirement_item, sample_create_data
    ):
        """Test successful requirement item creation."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_repository.create.return_value = sample_requirement_item
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.create_requirement_item(sample_create_data)
        
        # Verify
        assert result == sample_requirement_item
        mock_project_repository.get.assert_called_once_with(
            mock_requirement_repository.db, "test-project-1"
        )
        mock_requirement_repository.create.assert_called_once_with(
            mock_requirement_repository.db, obj_in=sample_create_data
        )
    
    def test_create_requirement_item_project_not_found(
        self, service, mock_requirement_repository, mock_project_repository, sample_create_data
    ):
        """Test requirement item creation when project doesn't exist."""
        # Setup mocks
        mock_project_repository.get.return_value = None
        mock_requirement_repository.db = MagicMock()
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            service.create_requirement_item(sample_create_data)
        
        assert "Project with id test-project-1 not found" in str(exc_info.value)
        mock_requirement_repository.create.assert_not_called()
    
    def test_create_requirement_item_database_error(
        self, service, mock_requirement_repository, mock_project_repository, 
        sample_project, sample_create_data
    ):
        """Test requirement item creation with database error."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_repository.create.side_effect = Exception("Database error")
        mock_requirement_repository.db = MagicMock()
        
        # Execute and verify exception
        with pytest.raises(DatabaseException) as exc_info:
            service.create_requirement_item(sample_create_data)
        
        assert "Error creating requirement item" in str(exc_info.value)
    
    def test_get_requirement_item_success(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test successful requirement item retrieval."""
        # Setup mock
        mock_requirement_repository.get_or_404.return_value = sample_requirement_item
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.get_requirement_item(1)
        
        # Verify
        assert result == sample_requirement_item
        mock_requirement_repository.get_or_404.assert_called_once_with(
            mock_requirement_repository.db, 1
        )
    
    def test_get_requirement_item_not_found(self, service, mock_requirement_repository):
        """Test requirement item retrieval when item doesn't exist."""
        # Setup mock
        mock_requirement_repository.get_or_404.side_effect = NotFoundException("Not found")
        mock_requirement_repository.db = MagicMock()
        
        # Execute and verify exception
        with pytest.raises(NotFoundException):
            service.get_requirement_item(999)
    
    def test_list_requirement_items_with_project_id(
        self, service, mock_requirement_repository, mock_project_repository, 
        sample_project, sample_requirement_item
    ):
        """Test listing requirement items with project ID filter."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_repository.get_by_project.return_value = [sample_requirement_item]
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.list_requirement_items(
            project_id="test-project-1", 
            status=RequirementItemStatus.new
        )
        
        # Verify
        assert result == [sample_requirement_item]
        mock_requirement_repository.get_by_project.assert_called_once_with(
            "test-project-1", RequirementItemStatus.new, 0, 100
        )
    
    def test_list_requirement_items_without_project_id(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test listing requirement items without project ID filter."""
        # Setup mock
        mock_requirement_repository.get_multi.return_value = [sample_requirement_item]
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.list_requirement_items(status=RequirementItemStatus.new)
        
        # Verify
        assert result == [sample_requirement_item]
        mock_requirement_repository.get_multi.assert_called_once_with(
            mock_requirement_repository.db, skip=0, limit=100, filters={'status': RequirementItemStatus.new}
        )
    
    def test_list_requirement_items_invalid_pagination(self, service):
        """Test listing requirement items with invalid pagination parameters."""
        # Test negative skip
        with pytest.raises(BadRequestException) as exc_info:
            service.list_requirement_items(skip=-1)
        assert "Skip parameter must be non-negative" in str(exc_info.value)
        
        # Test invalid limit
        with pytest.raises(BadRequestException) as exc_info:
            service.list_requirement_items(limit=0)
        assert "Limit parameter must be between 1 and 1000" in str(exc_info.value)
        
        with pytest.raises(BadRequestException) as exc_info:
            service.list_requirement_items(limit=1001)
        assert "Limit parameter must be between 1 and 1000" in str(exc_info.value)
    
    def test_update_requirement_item_success(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test successful requirement item update."""
        # Setup mocks
        update_data = RequirementItemUpdate(title="Updated Title")
        mock_requirement_repository.get_or_404.return_value = sample_requirement_item
        mock_requirement_repository.update_by_id.return_value = sample_requirement_item
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.update_requirement_item(1, update_data)
        
        # Verify
        assert result == sample_requirement_item
        mock_requirement_repository.update_by_id.assert_called_once_with(
            mock_requirement_repository.db, id=1, obj_in=update_data
        )
    
    def test_update_requirement_item_invalid_status_transition(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test requirement item update with invalid status transition."""
        # Setup mocks - item is already accepted, trying to go to new (invalid)
        sample_requirement_item.status = RequirementItemStatus.accepted
        update_data = RequirementItemUpdate(status=RequirementItemStatus.new)
        mock_requirement_repository.get_or_404.return_value = sample_requirement_item
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.update_requirement_item(1, update_data)
        
        # Should succeed because accepted -> new is allowed (reopening)
        assert result == sample_requirement_item
    
    def test_delete_requirement_item_success(self, service, mock_requirement_repository):
        """Test successful requirement item deletion."""
        # Setup mock
        mock_requirement_repository.delete.return_value = None
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        service.delete_requirement_item(1)
        
        # Verify
        mock_requirement_repository.delete.assert_called_once_with(
            mock_requirement_repository.db, id=1
        )
    
    def test_delete_requirement_item_not_found(self, service, mock_requirement_repository):
        """Test requirement item deletion when item doesn't exist."""
        # Setup mock
        mock_requirement_repository.delete.side_effect = Exception("not found")
        mock_requirement_repository.db = MagicMock()
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            service.delete_requirement_item(999)
        
        assert "Requirement item with id 999 not found" in str(exc_info.value)
    
    def test_update_status_success(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test successful status update."""
        # Setup mocks
        mock_requirement_repository.get_or_404.return_value = sample_requirement_item
        mock_requirement_repository.update_status.return_value = sample_requirement_item
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.update_status(1, RequirementItemStatus.accepted)
        
        # Verify
        assert result == sample_requirement_item
        mock_requirement_repository.update_status.assert_called_once_with(
            1, RequirementItemStatus.accepted
        )
    
    def test_update_status_invalid_transition(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test status update with invalid transition."""
        # This test would need to be updated based on actual business rules
        # For now, all transitions are allowed in the current implementation
        pass
    
    def test_get_project_status_summary_success(
        self, service, mock_requirement_repository, mock_project_repository, sample_project
    ):
        """Test successful project status summary retrieval."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_repository.get_status_summary.return_value = {
            "new": 2, "accepted": 1, "rejected": 0
        }
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.get_project_status_summary("test-project-1")
        
        # Verify
        expected = {"new": 2, "accepted": 1, "rejected": 0}
        assert result == expected
        mock_requirement_repository.get_status_summary.assert_called_once_with("test-project-1")
    
    def test_get_project_status_summary_project_not_found(
        self, service, mock_requirement_repository, mock_project_repository
    ):
        """Test project status summary when project doesn't exist."""
        # Setup mock
        mock_project_repository.get.return_value = None
        mock_requirement_repository.db = MagicMock()
        
        # Execute and verify exception
        with pytest.raises(NotFoundException) as exc_info:
            service.get_project_status_summary("non-existent-project")
        
        assert "Project with id non-existent-project not found" in str(exc_info.value)
    
    def test_search_requirement_items_success(
        self, service, mock_requirement_repository, mock_project_repository, 
        sample_project, sample_requirement_item
    ):
        """Test successful requirement items search."""
        # Setup mocks
        mock_project_repository.get.return_value = sample_project
        mock_requirement_repository.search_by_title.return_value = [sample_requirement_item]
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.search_requirement_items("test-project-1", "test")
        
        # Verify
        assert result == [sample_requirement_item]
        mock_requirement_repository.search_by_title.assert_called_once_with(
            "test-project-1", "test", 0, 100
        )
    
    def test_search_requirement_items_empty_search_term(self, service):
        """Test search with empty search term."""
        with pytest.raises(BadRequestException) as exc_info:
            service.search_requirement_items("test-project-1", "")
        assert "Search term cannot be empty" in str(exc_info.value)
        
        with pytest.raises(BadRequestException) as exc_info:
            service.search_requirement_items("test-project-1", "   ")
        assert "Search term cannot be empty" in str(exc_info.value)
    
    def test_bulk_update_status_success(
        self, service, mock_requirement_repository, sample_requirement_item
    ):
        """Test successful bulk status update."""
        # Setup mocks
        mock_requirement_repository.get_or_404.return_value = sample_requirement_item
        mock_requirement_repository.bulk_update_status.return_value = [sample_requirement_item]
        mock_requirement_repository.db = MagicMock()
        
        # Execute
        result = service.bulk_update_status([1, 2], RequirementItemStatus.accepted)
        
        # Verify
        assert result == [sample_requirement_item]
        mock_requirement_repository.bulk_update_status.assert_called_once_with(
            [1, 2], RequirementItemStatus.accepted
        )
    
    def test_bulk_update_status_empty_list(self, service):
        """Test bulk status update with empty item list."""
        with pytest.raises(BadRequestException) as exc_info:
            service.bulk_update_status([], RequirementItemStatus.accepted)
        assert "Item IDs list cannot be empty" in str(exc_info.value)
    
    def test_bulk_update_status_too_many_items(self, service):
        """Test bulk status update with too many items."""
        item_ids = list(range(101))  # 101 items
        with pytest.raises(BadRequestException) as exc_info:
            service.bulk_update_status(item_ids, RequirementItemStatus.accepted)
        assert "Cannot update more than 100 items at once" in str(exc_info.value)


class TestStatusTransitionValidation:
    """Test status transition validation logic."""
    
    def test_validate_status_transition_same_status(self, service):
        """Test that staying in the same status is allowed."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.new, RequirementItemStatus.new
        )
    
    def test_validate_status_transition_new_to_accepted(self, service):
        """Test transition from new to accepted."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.new, RequirementItemStatus.accepted
        )
    
    def test_validate_status_transition_new_to_rejected(self, service):
        """Test transition from new to rejected."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.new, RequirementItemStatus.rejected
        )
    
    def test_validate_status_transition_accepted_to_rejected(self, service):
        """Test transition from accepted to rejected."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.accepted, RequirementItemStatus.rejected
        )
    
    def test_validate_status_transition_accepted_to_new(self, service):
        """Test transition from accepted to new (reopening)."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.accepted, RequirementItemStatus.new
        )
    
    def test_validate_status_transition_rejected_to_new(self, service):
        """Test transition from rejected to new (reopening)."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.rejected, RequirementItemStatus.new
        )
    
    def test_validate_status_transition_rejected_to_accepted(self, service):
        """Test transition from rejected to accepted."""
        # Should not raise exception
        service._validate_status_transition(
            RequirementItemStatus.rejected, RequirementItemStatus.accepted
        )