"""Unit tests for RequirementItemRepository."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.repositories.requirement_item_repository import RequirementItemRepository
from app.domain.models.requirements import RequirementItem, RequirementItemStatus, RequirementItemPriority
from app.api.schemas.requirements import RequirementItemCreate, RequirementItemUpdate
from app.core.exceptions import NotFoundException, DatabaseException


@pytest.fixture
def mock_db_session():
    """Create a mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def repository(mock_db_session):
    """Create a RequirementItemRepository instance with mock session."""
    return RequirementItemRepository(mock_db_session)


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


class TestRequirementItemRepository:
    """Test RequirementItemRepository class."""
    
    def test_init(self, mock_db_session):
        """Test repository initialization."""
        repo = RequirementItemRepository(mock_db_session)
        assert repo.db == mock_db_session
        assert repo.model == RequirementItem
    
    def test_get_by_project_without_status_filter(self, repository, mock_db_session, sample_requirement_item):
        """Test getting requirement items by project without status filter."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_requirement_item]
        
        # Execute
        result = repository.get_by_project("test-project-1")
        
        # Verify
        assert len(result) == 1
        assert result[0] == sample_requirement_item
        mock_db_session.query.assert_called_once_with(RequirementItem)
        mock_query.filter.assert_called_once()
        mock_query.order_by.assert_called_once()
        mock_query.offset.assert_called_once_with(0)
        mock_query.limit.assert_called_once_with(100)
    
    def test_get_by_project_with_status_filter(self, repository, mock_db_session, sample_requirement_item):
        """Test getting requirement items by project with status filter."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_requirement_item]
        
        # Execute
        result = repository.get_by_project("test-project-1", RequirementItemStatus.new)
        
        # Verify
        assert len(result) == 1
        assert result[0] == sample_requirement_item
        # Should be called twice - once for project_id, once for status
        assert mock_query.filter.call_count == 2
    
    def test_get_by_project_with_pagination(self, repository, mock_db_session, sample_requirement_item):
        """Test getting requirement items with pagination."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_requirement_item]
        
        # Execute
        result = repository.get_by_project("test-project-1", skip=10, limit=20)
        
        # Verify
        mock_query.offset.assert_called_once_with(10)
        mock_query.limit.assert_called_once_with(20)
    
    def test_get_by_project_database_error(self, repository, mock_db_session):
        """Test database error handling in get_by_project."""
        # Setup mock to raise exception
        mock_db_session.query.side_effect = SQLAlchemyError("Database error")
        
        # Execute and verify exception
        with pytest.raises(DatabaseException) as exc_info:
            repository.get_by_project("test-project-1")
        
        assert "Error retrieving requirement items for project test-project-1" in str(exc_info.value)
    
    def test_get_by_project_and_status(self, repository, mock_db_session, sample_requirement_item):
        """Test getting requirement items by project and multiple statuses."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_requirement_item]
        
        # Execute
        statuses = [RequirementItemStatus.new, RequirementItemStatus.accepted]
        result = repository.get_by_project_and_status("test-project-1", statuses)
        
        # Verify
        assert len(result) == 1
        assert result[0] == sample_requirement_item
        mock_query.filter.assert_called_once()
    
    def test_count_by_project_without_status(self, repository, mock_db_session):
        """Test counting requirement items by project without status filter."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 5
        
        # Execute
        result = repository.count_by_project("test-project-1")
        
        # Verify
        assert result == 5
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_count_by_project_with_status(self, repository, mock_db_session):
        """Test counting requirement items by project with status filter."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 3
        
        # Execute
        result = repository.count_by_project("test-project-1", RequirementItemStatus.new)
        
        # Verify
        assert result == 3
        # Should be called twice - once for project_id, once for status
        assert mock_query.filter.call_count == 2
    
    def test_count_by_project_and_status(self, repository, mock_db_session):
        """Test counting requirement items by project and specific status."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.scalar.return_value = 2
        
        # Execute
        result = repository.count_by_project_and_status("test-project-1", RequirementItemStatus.accepted)
        
        # Verify
        assert result == 2
        mock_query.filter.assert_called_once()
        mock_query.scalar.assert_called_once()
    
    def test_update_status_success(self, repository, mock_db_session, sample_requirement_item):
        """Test successful status update."""
        # Setup mock
        with patch.object(repository, 'get_or_404', return_value=sample_requirement_item):
            # Execute
            result = repository.update_status(1, RequirementItemStatus.accepted)
            
            # Verify
            assert result == sample_requirement_item
            assert sample_requirement_item.status == RequirementItemStatus.accepted
            mock_db_session.commit.assert_called_once()
            mock_db_session.refresh.assert_called_once_with(sample_requirement_item)
    
    def test_update_status_not_found(self, repository, mock_db_session):
        """Test status update when item not found."""
        # Setup mock
        with patch.object(repository, 'get_or_404', side_effect=NotFoundException("Not found")):
            # Execute and verify exception
            with pytest.raises(NotFoundException):
                repository.update_status(999, RequirementItemStatus.accepted)
    
    def test_update_status_database_error(self, repository, mock_db_session, sample_requirement_item):
        """Test status update with database error."""
        # Setup mock
        with patch.object(repository, 'get_or_404', return_value=sample_requirement_item):
            mock_db_session.commit.side_effect = SQLAlchemyError("Database error")
            
            # Execute and verify exception
            with pytest.raises(DatabaseException) as exc_info:
                repository.update_status(1, RequirementItemStatus.accepted)
            
            assert "Error updating status for requirement item 1" in str(exc_info.value)
            mock_db_session.rollback.assert_called_once()
    
    def test_get_by_project_with_pagination_info(self, repository, mock_db_session, sample_requirement_item):
        """Test getting requirement items with pagination info."""
        # Setup mocks
        with patch.object(repository, 'get_by_project', return_value=[sample_requirement_item]) as mock_get:
            with patch.object(repository, 'count_by_project', return_value=10) as mock_count:
                # Execute
                items, total_count = repository.get_by_project_with_pagination_info("test-project-1", skip=5, limit=10)
                
                # Verify
                assert items == [sample_requirement_item]
                assert total_count == 10
                mock_get.assert_called_once_with("test-project-1", None, 5, 10)
                mock_count.assert_called_once_with("test-project-1", None)
    
    def test_get_status_summary(self, repository, mock_db_session):
        """Test getting status summary for a project."""
        # Setup mock
        with patch.object(repository, 'count_by_project_and_status') as mock_count:
            mock_count.side_effect = [2, 3, 1]  # new, accepted, rejected
            
            # Execute
            result = repository.get_status_summary("test-project-1")
            
            # Verify
            expected = {
                "new": 2,
                "accepted": 3,
                "rejected": 1
            }
            assert result == expected
            assert mock_count.call_count == 3
    
    def test_search_by_title(self, repository, mock_db_session, sample_requirement_item):
        """Test searching requirement items by title."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.offset.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_requirement_item]
        
        # Execute
        result = repository.search_by_title("test-project-1", "test")
        
        # Verify
        assert len(result) == 1
        assert result[0] == sample_requirement_item
        mock_query.filter.assert_called_once()
    
    def test_bulk_update_status(self, repository, mock_db_session):
        """Test bulk status update."""
        # Setup mock
        item1 = MagicMock()
        item2 = MagicMock()
        items = [item1, item2]
        
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = items
        
        # Execute
        result = repository.bulk_update_status([1, 2], RequirementItemStatus.accepted)
        
        # Verify
        assert result == items
        assert item1.status == RequirementItemStatus.accepted
        assert item2.status == RequirementItemStatus.accepted
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_any_call(item1)
        mock_db_session.refresh.assert_any_call(item2)
    
    def test_bulk_update_status_database_error(self, repository, mock_db_session):
        """Test bulk status update with database error."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [MagicMock()]
        mock_db_session.commit.side_effect = SQLAlchemyError("Database error")
        
        # Execute and verify exception
        with pytest.raises(DatabaseException) as exc_info:
            repository.bulk_update_status([1, 2], RequirementItemStatus.accepted)
        
        assert "Error bulk updating status for requirement items [1, 2]" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()
    
    def test_delete_by_project(self, repository, mock_db_session):
        """Test deleting all requirement items for a project."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 5
        mock_query.delete.return_value = None
        
        # Execute
        result = repository.delete_by_project("test-project-1")
        
        # Verify
        assert result == 5
        mock_db_session.commit.assert_called_once()
        mock_query.delete.assert_called_once()
    
    def test_delete_by_project_database_error(self, repository, mock_db_session):
        """Test delete by project with database error."""
        # Setup mock
        mock_query = MagicMock()
        mock_db_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.count.side_effect = SQLAlchemyError("Database error")
        
        # Execute and verify exception
        with pytest.raises(DatabaseException) as exc_info:
            repository.delete_by_project("test-project-1")
        
        assert "Error deleting requirement items for project test-project-1" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()


class TestRequirementItemRepositoryInheritedMethods:
    """Test inherited CRUD methods from base repository."""
    
    def test_create_method_inherited(self, repository):
        """Test that create method is inherited from base repository."""
        assert hasattr(repository, 'create')
        assert callable(repository.create)
    
    def test_get_method_inherited(self, repository):
        """Test that get method is inherited from base repository."""
        assert hasattr(repository, 'get')
        assert callable(repository.get)
    
    def test_get_or_404_method_inherited(self, repository):
        """Test that get_or_404 method is inherited from base repository."""
        assert hasattr(repository, 'get_or_404')
        assert callable(repository.get_or_404)
    
    def test_update_method_inherited(self, repository):
        """Test that update method is inherited from base repository."""
        assert hasattr(repository, 'update')
        assert callable(repository.update)
    
    def test_delete_method_inherited(self, repository):
        """Test that delete method is inherited from base repository."""
        assert hasattr(repository, 'delete')
        assert callable(repository.delete)