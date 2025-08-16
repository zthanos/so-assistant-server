"""Unit tests for SystemService."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.system_service import SystemService
from app.repositories.system_repository import SystemRepository
from app.repositories.project_repository import ProjectRepository
from app.domain.models.systems import System, SystemType
from app.domain.models.projects import Project
from app.api.schemas.systems import SystemCreate, SystemUpdate, SystemUpsert, SystemSearchFilters
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException


class TestSystemService:
    """Test cases for SystemService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_system_repo = Mock(spec=SystemRepository)
        self.mock_project_repo = Mock(spec=ProjectRepository)
        self.service = SystemService(self.mock_system_repo, self.mock_project_repo)
        self.mock_db = Mock(spec=Session)
        self.project_id = "test-project-123"
        
        # Sample data
        self.sample_project = Project(
            id=self.project_id,
            name="Test Project",
            description="A test project"
        )
        
        self.sample_system = System(
            id=1,
            project_id=self.project_id,
            name="Authentication System",
            description="Handles user authentication",
            type=SystemType.internal,
            dependencies=["Database", "Email Service"]
        )
    
    def test_create_system_success(self):
        """Test successful system creation."""
        # Arrange
        system_data = SystemCreate(
            project_id=self.project_id,
            name="New System",
            description="A new system",
            type=SystemType.internal,
            dependencies=["Database"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_by_project_and_name.return_value = None
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": True,
            "invalid_dependencies": [],
            "circular_dependencies": []
        }
        self.mock_system_repo.detect_circular_dependencies.return_value = []
        self.mock_system_repo.create.return_value = self.sample_system
        
        # Act
        result = self.service.create_system(self.mock_db, system_data)
        
        # Assert
        assert result.id == self.sample_system.id
        assert result.name == self.sample_system.name
        self.mock_project_repo.get.assert_called_once_with(self.mock_db, self.project_id)
        self.mock_system_repo.create.assert_called_once()
    
    def test_create_system_project_not_found(self):
        """Test system creation when project doesn't exist."""
        # Arrange
        system_data = SystemCreate(
            project_id=self.project_id,
            name="New System",
            type=SystemType.internal
        )
        
        self.mock_project_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            self.service.create_system(self.mock_db, system_data)
        
        assert "Project with id" in str(exc_info.value)
        self.mock_system_repo.create.assert_not_called()
    
    def test_create_system_duplicate_name(self):
        """Test system creation with duplicate name."""
        # Arrange
        system_data = SystemCreate(
            project_id=self.project_id,
            name="Existing System",
            type=SystemType.internal
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_by_project_and_name.return_value = self.sample_system
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_system(self.mock_db, system_data)
        
        assert "already exists" in str(exc_info.value)
        self.mock_system_repo.create.assert_not_called()
    
    def test_create_system_invalid_dependencies(self):
        """Test system creation with invalid dependencies."""
        # Arrange
        system_data = SystemCreate(
            project_id=self.project_id,
            name="New System",
            type=SystemType.internal,
            dependencies=["Nonexistent System"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_by_project_and_name.return_value = None
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": False,
            "invalid_dependencies": ["Nonexistent System"],
            "circular_dependencies": []
        }
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_system(self.mock_db, system_data)
        
        assert "Invalid dependencies" in str(exc_info.value)
        self.mock_system_repo.create.assert_not_called()
    
    def test_create_system_circular_dependencies(self):
        """Test system creation with circular dependencies."""
        # Arrange
        system_data = SystemCreate(
            project_id=self.project_id,
            name="System A",
            type=SystemType.internal,
            dependencies=["System B"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_by_project_and_name.return_value = None
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": True,
            "invalid_dependencies": [],
            "circular_dependencies": []
        }
        self.mock_system_repo.detect_circular_dependencies.return_value = ["System B"]
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_system(self.mock_db, system_data)
        
        assert "Circular dependencies detected" in str(exc_info.value)
        self.mock_system_repo.create.assert_not_called()
    
    def test_get_system_success(self):
        """Test successful system retrieval."""
        # Arrange
        system_id = 1
        self.mock_system_repo.get_or_404.return_value = self.sample_system
        
        # Act
        result = self.service.get_system(self.mock_db, system_id)
        
        # Assert
        assert result.id == self.sample_system.id
        assert result.name == self.sample_system.name
        self.mock_system_repo.get_or_404.assert_called_once_with(self.mock_db, system_id)
    
    def test_get_system_not_found(self):
        """Test system retrieval when system doesn't exist."""
        # Arrange
        system_id = 999
        self.mock_system_repo.get_or_404.side_effect = NotFoundException("System not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.get_system(self.mock_db, system_id)
    
    def test_upsert_system_create_new(self):
        """Test upserting a system that doesn't exist (create)."""
        # Arrange
        system_data = SystemUpsert(
            project_id=self.project_id,
            name="New System",
            type=SystemType.internal,
            dependencies=["Database"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": True,
            "invalid_dependencies": [],
            "circular_dependencies": []
        }
        self.mock_system_repo.detect_circular_dependencies.return_value = []
        self.mock_system_repo.upsert_system.return_value = self.sample_system
        
        # Act
        result = self.service.upsert_system(self.mock_db, system_data)
        
        # Assert
        assert result.id == self.sample_system.id
        self.mock_system_repo.upsert_system.assert_called_once()
    
    def test_upsert_system_update_existing(self):
        """Test upserting a system that exists (update)."""
        # Arrange
        system_data = SystemUpsert(
            project_id=self.project_id,
            name="Existing System",
            type=SystemType.external,
            dependencies=["New Dependency"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": True,
            "invalid_dependencies": [],
            "circular_dependencies": []
        }
        self.mock_system_repo.detect_circular_dependencies.return_value = []
        self.mock_system_repo.upsert_system.return_value = self.sample_system
        
        # Act
        result = self.service.upsert_system(self.mock_db, system_data)
        
        # Assert
        assert result.id == self.sample_system.id
        self.mock_system_repo.upsert_system.assert_called_once()
    
    def test_update_system_success(self):
        """Test successful system update."""
        # Arrange
        system_id = 1
        system_data = SystemUpdate(
            name="Updated System",
            description="Updated description",
            dependencies=["New Dependency"]
        )
        
        self.mock_system_repo.get_or_404.return_value = self.sample_system
        self.mock_system_repo.get_by_project_and_name.return_value = None
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": True,
            "invalid_dependencies": [],
            "circular_dependencies": []
        }
        self.mock_system_repo.detect_circular_dependencies.return_value = []
        self.mock_system_repo.update_by_id.return_value = self.sample_system
        
        # Act
        result = self.service.update_system(self.mock_db, system_id, system_data)
        
        # Assert
        assert result.id == self.sample_system.id
        self.mock_system_repo.update_by_id.assert_called_once()
    
    def test_update_system_duplicate_name(self):
        """Test system update with duplicate name."""
        # Arrange
        system_id = 1
        system_data = SystemUpdate(name="Duplicate Name")
        
        existing_system = Mock()
        existing_system.name = "Original Name"
        existing_system.project_id = self.project_id
        
        duplicate_system = Mock()
        duplicate_system.id = 2
        
        self.mock_system_repo.get_or_404.return_value = existing_system
        self.mock_system_repo.get_by_project_and_name.return_value = duplicate_system
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.update_system(self.mock_db, system_id, system_data)
        
        assert "already exists" in str(exc_info.value)
        self.mock_system_repo.update_by_id.assert_not_called()
    
    def test_delete_system_success(self):
        """Test successful system deletion."""
        # Arrange
        system_id = 1
        self.mock_system_repo.get_or_404.return_value = self.sample_system
        
        # Act
        result = self.service.delete_system(self.mock_db, system_id)
        
        # Assert
        assert result is True
        self.mock_system_repo.delete.assert_called_once_with(self.mock_db, id=system_id)
    
    def test_delete_system_not_found(self):
        """Test system deletion when system doesn't exist."""
        # Arrange
        system_id = 999
        self.mock_system_repo.get_or_404.side_effect = NotFoundException("System not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.delete_system(self.mock_db, system_id)
        
        self.mock_system_repo.delete.assert_not_called()
    
    def test_list_systems_success(self):
        """Test successful system listing."""
        # Arrange
        systems = [self.sample_system]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_by_project.return_value = systems
        
        # Act
        result = self.service.list_systems(self.mock_db, self.project_id)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == self.sample_system.id
        self.mock_system_repo.get_by_project.assert_called_once()
    
    def test_list_systems_with_filters(self):
        """Test system listing with filters."""
        # Arrange
        filters = SystemSearchFilters(name="auth", type=SystemType.internal)
        systems = [self.sample_system]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.search_systems.return_value = systems
        
        # Act
        result = self.service.list_systems(self.mock_db, self.project_id, filters)
        
        # Assert
        assert len(result) == 1
        self.mock_system_repo.search_systems.assert_called_once()
    
    def test_list_systems_project_not_found(self):
        """Test system listing when project doesn't exist."""
        # Arrange
        self.mock_project_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.list_systems(self.mock_db, self.project_id)
    
    def test_validate_system_dependencies_success(self):
        """Test successful dependency validation."""
        # Arrange
        dependencies = ["System A", "System B"]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": True,
            "invalid_dependencies": [],
            "circular_dependencies": []
        }
        
        # Act
        result = self.service.validate_system_dependencies(self.mock_db, self.project_id, dependencies)
        
        # Assert
        assert result.valid is True
        assert result.invalid_dependencies == []
        assert result.circular_dependencies == []
    
    def test_validate_system_dependencies_invalid(self):
        """Test dependency validation with invalid dependencies."""
        # Arrange
        dependencies = ["System A", "Nonexistent System"]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.validate_dependencies.return_value = {
            "valid": False,
            "invalid_dependencies": ["Nonexistent System"],
            "circular_dependencies": []
        }
        
        # Act
        result = self.service.validate_system_dependencies(self.mock_db, self.project_id, dependencies)
        
        # Assert
        assert result.valid is False
        assert "Nonexistent System" in result.invalid_dependencies
    
    def test_get_systems_by_type_success(self):
        """Test successful retrieval of systems by type."""
        # Arrange
        system_type = SystemType.internal
        systems = [self.sample_system]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_systems_by_type.return_value = systems
        
        # Act
        result = self.service.get_systems_by_type(self.mock_db, self.project_id, system_type)
        
        # Assert
        assert len(result) == 1
        assert result[0].type == system_type
        self.mock_system_repo.get_systems_by_type.assert_called_once()
    
    def test_get_systems_with_dependencies_success(self):
        """Test successful retrieval of systems with dependencies."""
        # Arrange
        systems = [self.sample_system]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.get_systems_with_dependencies.return_value = systems
        
        # Act
        result = self.service.get_systems_with_dependencies(self.mock_db, self.project_id)
        
        # Assert
        assert len(result) == 1
        assert len(result[0].dependencies) > 0
        self.mock_system_repo.get_systems_with_dependencies.assert_called_once()
    
    def test_count_systems_success(self):
        """Test successful system counting."""
        # Arrange
        expected_count = 5
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.count_by_project.return_value = expected_count
        
        # Act
        result = self.service.count_systems(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_count
        self.mock_system_repo.count_by_project.assert_called_once()
    
    def test_count_systems_with_filters(self):
        """Test system counting with filters."""
        # Arrange
        filters = SystemSearchFilters(type=SystemType.internal)
        expected_count = 3
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_system_repo.count_by_project.return_value = expected_count
        
        # Act
        result = self.service.count_systems(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_count
        self.mock_system_repo.count_by_project.assert_called_once_with(self.mock_db, self.project_id, filters)
    
    def test_to_response_conversion(self):
        """Test conversion from System model to SystemResponse."""
        # Act
        result = self.service._to_response(self.sample_system)
        
        # Assert
        assert result.id == self.sample_system.id
        assert result.project_id == self.sample_system.project_id
        assert result.name == self.sample_system.name
        assert result.description == self.sample_system.description
        assert result.type == self.sample_system.type
        assert result.dependencies == self.sample_system.dependencies
        assert result.created_at == self.sample_system.created_at
        assert result.updated_at == self.sample_system.updated_at
    
    def test_database_error_handling(self):
        """Test general database error handling."""
        # Arrange
        system_data = SystemCreate(
            project_id=self.project_id,
            name="Test System",
            type=SystemType.internal
        )
        
        self.mock_project_repo.get.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(DatabaseException):
            self.service.create_system(self.mock_db, system_data)