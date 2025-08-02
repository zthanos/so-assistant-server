"""Tests for the TeamService.

This module contains unit tests for the TeamService class.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.services.teams import TeamService
from app.domain.models.teams import Team
from app.api.schemas.teams import TeamCreate, TeamUpdate
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams, PaginationResult, SortOrder

class TestTeamService:
    """Test cases for the TeamService class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.team_repository = MagicMock()
        self.project_repository = MagicMock()
        
        # Create service with mocked dependencies
        self.service = TeamService(self.db)
        self.service.team_repository = self.team_repository
        self.service.project_repository = self.project_repository
        
        # Mock project
        self.project_id = "test-project"
        self.project = MagicMock()
        self.project.id = self.project_id
        
        # Mock Team
        self.team = MagicMock(spec=Team)
        self.team.id = 1
        self.team.project_id = self.project_id
        self.team.name = "Test Team"
        self.team.members = "John Doe, Jane Smith"

    def test_create_team(self):
        """Test creating a team."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.team_repository.get_by_name.return_value = None
        self.team_repository.create.return_value = self.team
        
        # Act
        result = self.service.create_team(self.project_id, "Test Team", "John Doe, Jane Smith")
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.team_repository.get_by_name.assert_called_once_with(
            self.db, project_id=self.project_id, name="Test Team"
        )
        self.team_repository.create.assert_called_once()
        assert result == self.team
    
    def test_create_team_project_not_found(self):
        """Test creating a team when the project is not found."""
        # Arrange
        self.project_repository.get_or_404.side_effect = NotFoundException("Project not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.create_team(self.project_id, "Test Team", "John Doe, Jane Smith")
    
    def test_create_team_name_conflict(self):
        """Test creating a team with a name that already exists."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.team_repository.get_by_name.return_value = self.team
        
        # Act & Assert
        with pytest.raises(ConflictException):
            self.service.create_team(self.project_id, "Test Team", "John Doe, Jane Smith")
    
    def test_get_team(self):
        """Test getting a team by ID."""
        # Arrange
        self.team_repository.get_or_404.return_value = self.team
        
        # Act
        result = self.service.get_team(1)
        
        # Assert
        self.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        assert result == self.team
    
    def test_get_team_with_tasks(self):
        """Test getting a team with tasks."""
        # Arrange
        self.team_repository.get_with_tasks.return_value = self.team
        
        # Act
        result = self.service.get_team_with_tasks(1)
        
        # Assert
        self.team_repository.get_with_tasks.assert_called_once_with(self.db, id=1)
        assert result == self.team
    
    def test_get_team_with_tasks_not_found(self):
        """Test getting a team with tasks when the team is not found."""
        # Arrange
        self.team_repository.get_with_tasks.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.get_team_with_tasks(1)
    
    def test_get_teams_for_project(self):
        """Test getting teams for a project with pagination."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        pagination = PaginationParams(page=1, per_page=20)
        
        # Mock the query and pagination result
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        expected_result = PaginationResult(
            items=[self.team],
            total=1,
            page=1,
            per_page=20,
            pages=1,
            has_next=False,
            has_prev=False
        )
        
        with patch('app.services.teams.Paginator.paginate_query', return_value=expected_result):
            # Act
            result = self.service.get_teams_for_project(self.project_id, pagination)
            
            # Assert
            self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
            assert result == expected_result

    def test_update_team(self):
        """Test updating a team."""
        # Arrange
        updated_team = MagicMock(spec=Team)
        self.team_repository.get_or_404.return_value = self.team
        self.team_repository.get_by_name.return_value = None
        self.team_repository.update.return_value = updated_team
        
        # Act
        result = self.service.update_team(1, "Updated Team", "John Doe, Jane Smith, Bob Johnson")
        
        # Assert
        self.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.team_repository.get_by_name.assert_called_once_with(
            self.db, project_id=self.team.project_id, name="Updated Team"
        )
        self.team_repository.update.assert_called_once()
        assert result == updated_team
    
    def test_update_team_no_fields(self):
        """Test updating a team with no fields provided."""
        # Arrange
        self.team_repository.get_or_404.return_value = self.team
        
        # Act & Assert
        with pytest.raises(BadRequestException):
            self.service.update_team(1)
    
    def test_update_team_name_conflict(self):
        """Test updating a team with a name that already exists."""
        # Arrange
        self.team_repository.get_or_404.return_value = self.team
        
        conflicting_team = MagicMock(spec=Team)
        conflicting_team.id = 2  # Different ID
        
        self.team_repository.get_by_name.return_value = conflicting_team
        
        # Act & Assert
        with pytest.raises(ConflictException):
            self.service.update_team(1, "Updated Team", "John Doe, Jane Smith, Bob Johnson")
    
    def test_update_team_same_name(self):
        """Test updating a team with the same name."""
        # Arrange
        updated_team = MagicMock(spec=Team)
        self.team_repository.get_or_404.return_value = self.team
        self.team_repository.update.return_value = updated_team
        
        # Act
        result = self.service.update_team(1, "Test Team", "John Doe, Jane Smith, Bob Johnson")
        
        # Assert
        self.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.team_repository.get_by_name.assert_not_called()
        self.team_repository.update.assert_called_once()
        assert result == updated_team
    
    def test_delete_team(self):
        """Test deleting a team."""
        # Arrange
        self.team_repository.get_or_404.return_value = self.team
        self.team_repository.delete.return_value = self.team
        
        # Act
        result = self.service.delete_team(1)
        
        # Assert
        self.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.team_repository.delete.assert_called_once_with(self.db, id=1)
        assert result == self.team

    def test_search_teams(self):
        """Test searching teams with pagination."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        pagination = PaginationParams(page=1, per_page=20)
        
        # Mock the query and pagination result
        mock_query = MagicMock()
        self.db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        
        expected_result = PaginationResult(
            items=[self.team],
            total=1,
            page=1,
            per_page=20,
            pages=1,
            has_next=False,
            has_prev=False
        )
        
        with patch('app.services.teams.Paginator.paginate_query', return_value=expected_result):
            with patch('app.services.teams.QueryFilter.apply_search'):
                # Act
                result = self.service.search_teams(self.project_id, "test", pagination)
                
                # Assert
                self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
                assert result == expected_result
    
    def test_count_teams_for_project(self):
        """Test counting teams for a project."""
        # Arrange
        self.project_repository.get_or_404.return_value = self.project
        self.team_repository.count_by_project.return_value = 5
        
        # Act
        result = self.service.count_teams_for_project(self.project_id)
        
        # Assert
        self.project_repository.get_or_404.assert_called_once_with(self.db, self.project_id)
        self.team_repository.count_by_project.assert_called_once_with(self.db, project_id=self.project_id)
        assert result == 5