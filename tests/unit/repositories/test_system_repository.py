"""Unit tests for SystemRepository."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.repositories.system_repository import SystemRepository
from app.domain.models.systems import System, SystemType
from app.api.schemas.systems import SystemCreate, SystemUpdate, SystemSearchFilters
from app.core.exceptions import DatabaseException, BadRequestException


class TestSystemRepository:
    """Test cases for SystemRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = SystemRepository()
        self.mock_db = Mock(spec=Session)
        self.project_id = "test-project-123"
        
        # Sample system data
        self.sample_system = System(
            id=1,
            project_id=self.project_id,
            name="Authentication System",
            description="Handles user authentication",
            type=SystemType.internal,
            dependencies=["Database", "Email Service"]
        )
    
    def test_init(self):
        """Test repository initialization."""
        assert self.repository.model == System
    
    def test_get_by_project_success(self):
        """Test successful retrieval of systems by project."""
        # Arrange
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_systems
        self.mock_db.query.assert_called_once_with(System)
        mock_query.filter.assert_called_once()
    
    def test_get_by_project_with_pagination(self):
        """Test retrieval of systems by project with pagination."""
        # Arrange
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project(self.mock_db, self.project_id, skip=10, limit=20)
        
        # Assert
        assert result == expected_systems
        mock_query.filter.return_value.offset.assert_called_with(10)
        mock_query.filter.return_value.offset.return_value.limit.assert_called_with(20)
    
    def test_get_by_project_database_error(self):
        """Test database error handling in get_by_project."""
        # Arrange
        self.mock_db.query.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(DatabaseException) as exc_info:
            self.repository.get_by_project(self.mock_db, self.project_id)
        
        assert "Error retrieving systems" in str(exc_info.value)
    
    def test_get_by_project_and_name_success(self):
        """Test successful retrieval of system by project and name."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = self.sample_system
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project_and_name(self.mock_db, self.project_id, "Authentication System")
        
        # Assert
        assert result == self.sample_system
        self.mock_db.query.assert_called_once_with(System)
    
    def test_get_by_project_and_name_not_found(self):
        """Test retrieval when system is not found."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project_and_name(self.mock_db, self.project_id, "Nonexistent System")
        
        # Assert
        assert result is None
    
    def test_search_systems_with_name_filter(self):
        """Test searching systems with name filter."""
        # Arrange
        filters = SystemSearchFilters(name="auth")
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_systems(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_systems
        # Verify that filter was called multiple times (project_id and name)
        assert mock_query.filter.call_count >= 1
    
    def test_search_systems_with_type_filter(self):
        """Test searching systems with type filter."""
        # Arrange
        filters = SystemSearchFilters(type=SystemType.internal)
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_systems(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_systems
    
    def test_search_systems_with_has_dependencies_true(self):
        """Test searching systems that have dependencies."""
        # Arrange
        filters = SystemSearchFilters(has_dependencies=True)
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_systems(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_systems
    
    def test_search_systems_with_has_dependencies_false(self):
        """Test searching systems that don't have dependencies."""
        # Arrange
        filters = SystemSearchFilters(has_dependencies=False)
        expected_systems = []
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_systems(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_systems
    
    def test_count_by_project_success(self):
        """Test counting systems by project."""
        # Arrange
        expected_count = 5
        mock_query = Mock()
        mock_query.filter.return_value.scalar.return_value = expected_count
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.count_by_project(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_count
    
    def test_count_by_project_with_filters(self):
        """Test counting systems by project with filters."""
        # Arrange
        filters = SystemSearchFilters(name="auth", type=SystemType.internal)
        expected_count = 2
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = expected_count
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.count_by_project(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_count
    
    def test_validate_dependencies_valid(self):
        """Test dependency validation with valid dependencies."""
        # Arrange
        dependencies = ["Database", "Email Service"]
        mock_systems = [Mock(name="Database"), Mock(name="Email Service"), Mock(name="Other System")]
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_systems
        
        # Act
        result = self.repository.validate_dependencies(self.mock_db, self.project_id, dependencies)
        
        # Assert
        assert result["valid"] is True
        assert result["invalid_dependencies"] == []
        assert result["circular_dependencies"] == []
    
    def test_validate_dependencies_invalid(self):
        """Test dependency validation with invalid dependencies."""
        # Arrange
        dependencies = ["Database", "Nonexistent System"]
        mock_systems = [Mock(name="Database"), Mock(name="Email Service")]
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_systems
        
        # Act
        result = self.repository.validate_dependencies(self.mock_db, self.project_id, dependencies)
        
        # Assert
        assert result["valid"] is False
        assert "Nonexistent System" in result["invalid_dependencies"]
        assert "Database" not in result["invalid_dependencies"]
    
    def test_validate_dependencies_empty_list(self):
        """Test dependency validation with empty dependencies list."""
        # Arrange
        dependencies = []
        
        # Act
        result = self.repository.validate_dependencies(self.mock_db, self.project_id, dependencies)
        
        # Assert
        assert result["valid"] is True
        assert result["invalid_dependencies"] == []
        assert result["circular_dependencies"] == []
    
    def test_detect_circular_dependencies_no_circular(self):
        """Test circular dependency detection with no circular dependencies."""
        # Arrange
        system_name = "System A"
        new_dependencies = ["System B", "System C"]
        
        mock_systems = [
            Mock(name="System A", dependencies=[]),
            Mock(name="System B", dependencies=["System C"]),
            Mock(name="System C", dependencies=[])
        ]
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_systems
        
        # Act
        result = self.repository.detect_circular_dependencies(
            self.mock_db, self.project_id, system_name, new_dependencies
        )
        
        # Assert
        assert result == []
    
    def test_detect_circular_dependencies_with_circular(self):
        """Test circular dependency detection with circular dependencies."""
        # Arrange
        system_name = "System A"
        new_dependencies = ["System B"]
        
        mock_systems = [
            Mock(name="System A", dependencies=[]),
            Mock(name="System B", dependencies=["System A"])  # This creates a circular dependency
        ]
        self.mock_db.query.return_value.filter.return_value.all.return_value = mock_systems
        
        # Act
        result = self.repository.detect_circular_dependencies(
            self.mock_db, self.project_id, system_name, new_dependencies
        )
        
        # Assert
        assert "System B" in result
    
    def test_upsert_system_create_new(self):
        """Test upserting a system that doesn't exist (create)."""
        # Arrange
        system_name = "New System"
        system_data = {
            "description": "A new system",
            "type": SystemType.internal,
            "dependencies": ["Database"]
        }
        
        # Mock get_by_project_and_name to return None (system doesn't exist)
        with patch.object(self.repository, 'get_by_project_and_name', return_value=None):
            with patch.object(self.repository, 'detect_circular_dependencies', return_value=[]):
                # Act
                result = self.repository.upsert_system(
                    self.mock_db, self.project_id, system_name, system_data
                )
                
                # Assert
                self.mock_db.add.assert_called_once()
                self.mock_db.commit.assert_called_once()
                self.mock_db.refresh.assert_called_once()
    
    def test_upsert_system_update_existing(self):
        """Test upserting a system that exists (update)."""
        # Arrange
        system_name = "Existing System"
        system_data = {
            "description": "Updated description",
            "type": SystemType.external,
            "dependencies": ["New Dependency"]
        }
        
        existing_system = Mock()
        existing_system.description = "Old description"
        existing_system.type = SystemType.internal
        existing_system.dependencies = ["Old Dependency"]
        
        # Mock get_by_project_and_name to return existing system
        with patch.object(self.repository, 'get_by_project_and_name', return_value=existing_system):
            with patch.object(self.repository, 'detect_circular_dependencies', return_value=[]):
                # Act
                result = self.repository.upsert_system(
                    self.mock_db, self.project_id, system_name, system_data
                )
                
                # Assert
                assert existing_system.description == "Updated description"
                assert existing_system.type == SystemType.external
                assert existing_system.dependencies == ["New Dependency"]
                self.mock_db.add.assert_called_once_with(existing_system)
                self.mock_db.commit.assert_called_once()
                self.mock_db.refresh.assert_called_once_with(existing_system)
    
    def test_upsert_system_circular_dependency_error(self):
        """Test upserting a system with circular dependencies."""
        # Arrange
        system_name = "System A"
        system_data = {
            "description": "A system",
            "type": SystemType.internal,
            "dependencies": ["System B"]
        }
        
        # Mock detect_circular_dependencies to return circular dependency
        with patch.object(self.repository, 'detect_circular_dependencies', return_value=["System B"]):
            # Act & Assert
            with pytest.raises(BadRequestException) as exc_info:
                self.repository.upsert_system(
                    self.mock_db, self.project_id, system_name, system_data
                )
            
            assert "Circular dependencies detected" in str(exc_info.value)
    
    def test_delete_by_project_and_name_success(self):
        """Test successful deletion of system by project and name."""
        # Arrange
        system_name = "System to Delete"
        
        # Mock get_by_project_and_name to return a system
        with patch.object(self.repository, 'get_by_project_and_name', return_value=self.sample_system):
            # Act
            result = self.repository.delete_by_project_and_name(
                self.mock_db, self.project_id, system_name
            )
            
            # Assert
            assert result is True
            self.mock_db.delete.assert_called_once_with(self.sample_system)
            self.mock_db.commit.assert_called_once()
    
    def test_delete_by_project_and_name_not_found(self):
        """Test deletion when system is not found."""
        # Arrange
        system_name = "Nonexistent System"
        
        # Mock get_by_project_and_name to return None
        with patch.object(self.repository, 'get_by_project_and_name', return_value=None):
            # Act
            result = self.repository.delete_by_project_and_name(
                self.mock_db, self.project_id, system_name
            )
            
            # Assert
            assert result is False
            self.mock_db.delete.assert_not_called()
            self.mock_db.commit.assert_not_called()
    
    def test_get_systems_by_type_success(self):
        """Test retrieval of systems by type."""
        # Arrange
        system_type = SystemType.internal
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_systems_by_type(self.mock_db, self.project_id, system_type)
        
        # Assert
        assert result == expected_systems
        self.mock_db.query.assert_called_once_with(System)
    
    def test_get_systems_with_dependencies_success(self):
        """Test retrieval of systems with dependencies."""
        # Arrange
        expected_systems = [self.sample_system]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_systems
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_systems_with_dependencies(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_systems
        self.mock_db.query.assert_called_once_with(System)
    
    def test_database_error_handling(self):
        """Test general database error handling."""
        # Arrange
        self.mock_db.query.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(DatabaseException):
            self.repository.get_by_project(self.mock_db, self.project_id)
        
        with pytest.raises(DatabaseException):
            self.repository.get_by_project_and_name(self.mock_db, self.project_id, "test")
        
        with pytest.raises(DatabaseException):
            filters = SystemSearchFilters()
            self.repository.search_systems(self.mock_db, self.project_id, filters)