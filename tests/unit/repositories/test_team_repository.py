"""Unit tests for TeamRepository."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.repositories.team_repository import TeamRepository
from app.domain.models.teams import Team
from app.api.schemas.teams import TeamCreate, TeamUpdate, TeamSearchFilters
from app.core.exceptions import DatabaseException


class TestTeamRepository:
    """Test cases for TeamRepository."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.repository = TeamRepository()
        self.mock_db = Mock(spec=Session)
        self.project_id = "test-project-123"
        
        # Sample team data
        self.sample_team = Team(
            id=1,
            project_id=self.project_id,
            name="Backend Team",
            role="Development Team",
            members=["Alice Johnson", "Bob Smith", "Carol Davis"],
            responsibilities=["API Development", "Database Design", "Security Implementation"]
        )
    
    def test_init(self):
        """Test repository initialization."""
        assert self.repository.model == Team
    
    def test_get_by_project_success(self):
        """Test successful retrieval of teams by project."""
        # Arrange
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_teams
        self.mock_db.query.assert_called_once_with(Team)
        mock_query.filter.assert_called_once()
    
    def test_get_by_project_with_pagination(self):
        """Test retrieval of teams by project with pagination."""
        # Arrange
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project(self.mock_db, self.project_id, skip=10, limit=20)
        
        # Assert
        assert result == expected_teams
        mock_query.filter.return_value.order_by.return_value.offset.assert_called_with(10)
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.assert_called_with(20)
    
    def test_get_by_project_database_error(self):
        """Test database error handling in get_by_project."""
        # Arrange
        self.mock_db.query.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(DatabaseException) as exc_info:
            self.repository.get_by_project(self.mock_db, self.project_id)
        
        assert "Error retrieving teams" in str(exc_info.value)
    
    def test_get_by_project_and_name_success(self):
        """Test successful retrieval of team by project and name."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = self.sample_team
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project_and_name(self.mock_db, self.project_id, "Backend Team")
        
        # Assert
        assert result == self.sample_team
        self.mock_db.query.assert_called_once_with(Team)
    
    def test_get_by_project_and_name_not_found(self):
        """Test retrieval when team is not found."""
        # Arrange
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_by_project_and_name(self.mock_db, self.project_id, "Nonexistent Team")
        
        # Assert
        assert result is None
    
    def test_search_teams_with_name_filter(self):
        """Test searching teams with name filter."""
        # Arrange
        filters = TeamSearchFilters(name="backend")
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_teams(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_teams
        # Verify that filter was called multiple times (project_id and name)
        assert mock_query.filter.call_count >= 1
    
    def test_search_teams_with_role_filter(self):
        """Test searching teams with role filter."""
        # Arrange
        filters = TeamSearchFilters(role="development")
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_teams(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_teams
    
    def test_search_teams_with_member_filter(self):
        """Test searching teams with member filter."""
        # Arrange
        filters = TeamSearchFilters(member="alice")
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_teams(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_teams
    
    def test_search_teams_with_responsibility_filter(self):
        """Test searching teams with responsibility filter."""
        # Arrange
        filters = TeamSearchFilters(responsibility="api")
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.search_teams(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_teams
    
    def test_count_by_project_success(self):
        """Test counting teams by project."""
        # Arrange
        expected_count = 3
        mock_query = Mock()
        mock_query.filter.return_value.scalar.return_value = expected_count
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.count_by_project(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_count
    
    def test_count_by_project_with_filters(self):
        """Test counting teams by project with filters."""
        # Arrange
        filters = TeamSearchFilters(name="backend", role="development")
        expected_count = 1
        mock_query = Mock()
        mock_query.filter.return_value.filter.return_value.filter.return_value.scalar.return_value = expected_count
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.count_by_project(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_count
    
    def test_validate_member_names_valid(self):
        """Test member name validation with valid names."""
        # Arrange
        members = ["Alice Johnson", "Bob Smith", "Carol Davis"]
        
        # Act
        result = self.repository.validate_member_names(members)
        
        # Assert
        assert result["valid"] is True
        assert result["invalid_members"] == []
        assert result["duplicate_members"] == []
    
    def test_validate_member_names_with_duplicates(self):
        """Test member name validation with duplicate names."""
        # Arrange
        members = ["Alice Johnson", "Bob Smith", "Alice Johnson"]
        
        # Act
        result = self.repository.validate_member_names(members)
        
        # Assert
        assert result["valid"] is False
        assert "Alice Johnson" in result["duplicate_members"]
        assert "Bob Smith" not in result["duplicate_members"]
    
    def test_validate_member_names_with_invalid_names(self):
        """Test member name validation with invalid names."""
        # Arrange
        members = ["Alice Johnson", "", "   ", "Bob Smith"]
        
        # Act
        result = self.repository.validate_member_names(members)
        
        # Assert
        assert result["valid"] is False
        assert "" in result["invalid_members"]
        assert "   " in result["invalid_members"]
        assert "Alice Johnson" not in result["invalid_members"]
        assert "Bob Smith" not in result["invalid_members"]
    
    def test_validate_member_names_empty_list(self):
        """Test member name validation with empty list."""
        # Arrange
        members = []
        
        # Act
        result = self.repository.validate_member_names(members)
        
        # Assert
        assert result["valid"] is True
        assert result["invalid_members"] == []
        assert result["duplicate_members"] == []
    
    def test_upsert_team_create_new(self):
        """Test upserting a team that doesn't exist (create)."""
        # Arrange
        team_name = "New Team"
        team_data = {
            "role": "Development Team",
            "members": ["Alice", "Bob"],
            "responsibilities": ["Coding", "Testing"]
        }
        
        # Mock get_by_project_and_name to return None (team doesn't exist)
        with patch.object(self.repository, 'get_by_project_and_name', return_value=None):
            with patch.object(self.repository, 'validate_member_names', return_value={"valid": True, "invalid_members": [], "duplicate_members": []}):
                # Act
                result = self.repository.upsert_team(
                    self.mock_db, self.project_id, team_name, team_data
                )
                
                # Assert
                self.mock_db.add.assert_called_once()
                self.mock_db.commit.assert_called_once()
                self.mock_db.refresh.assert_called_once()
    
    def test_upsert_team_update_existing(self):
        """Test upserting a team that exists (update)."""
        # Arrange
        team_name = "Existing Team"
        team_data = {
            "role": "Updated Role",
            "members": ["Alice", "Bob", "Charlie"],
            "responsibilities": ["New Responsibility"]
        }
        
        existing_team = Mock()
        existing_team.role = "Old Role"
        existing_team.members = ["Alice", "Bob"]
        existing_team.responsibilities = ["Old Responsibility"]
        
        # Mock get_by_project_and_name to return existing team
        with patch.object(self.repository, 'get_by_project_and_name', return_value=existing_team):
            with patch.object(self.repository, 'validate_member_names', return_value={"valid": True, "invalid_members": [], "duplicate_members": []}):
                # Act
                result = self.repository.upsert_team(
                    self.mock_db, self.project_id, team_name, team_data
                )
                
                # Assert
                assert existing_team.role == "Updated Role"
                assert existing_team.members == ["Alice", "Bob", "Charlie"]
                assert existing_team.responsibilities == ["New Responsibility"]
                self.mock_db.add.assert_called_once_with(existing_team)
                self.mock_db.commit.assert_called_once()
                self.mock_db.refresh.assert_called_once_with(existing_team)
    
    def test_upsert_team_invalid_members_error(self):
        """Test upserting a team with invalid members."""
        # Arrange
        team_name = "Team A"
        team_data = {
            "role": "Development",
            "members": ["Alice", "", "Bob"],
            "responsibilities": ["Coding"]
        }
        
        # Mock validate_member_names to return invalid result
        with patch.object(self.repository, 'validate_member_names', return_value={"valid": False, "invalid_members": [""], "duplicate_members": []}):
            # Act & Assert
            with pytest.raises(DatabaseException) as exc_info:
                self.repository.upsert_team(
                    self.mock_db, self.project_id, team_name, team_data
                )
            
            assert "Member validation failed" in str(exc_info.value)
    
    def test_delete_by_project_and_name_success(self):
        """Test successful deletion of team by project and name."""
        # Arrange
        team_name = "Team to Delete"
        
        # Mock get_by_project_and_name to return a team
        with patch.object(self.repository, 'get_by_project_and_name', return_value=self.sample_team):
            # Act
            result = self.repository.delete_by_project_and_name(
                self.mock_db, self.project_id, team_name
            )
            
            # Assert
            assert result is True
            self.mock_db.delete.assert_called_once_with(self.sample_team)
            self.mock_db.commit.assert_called_once()
    
    def test_delete_by_project_and_name_not_found(self):
        """Test deletion when team is not found."""
        # Arrange
        team_name = "Nonexistent Team"
        
        # Mock get_by_project_and_name to return None
        with patch.object(self.repository, 'get_by_project_and_name', return_value=None):
            # Act
            result = self.repository.delete_by_project_and_name(
                self.mock_db, self.project_id, team_name
            )
            
            # Assert
            assert result is False
            self.mock_db.delete.assert_not_called()
            self.mock_db.commit.assert_not_called()
    
    def test_get_teams_by_role_success(self):
        """Test retrieval of teams by role."""
        # Arrange
        role = "development"
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_teams_by_role(self.mock_db, self.project_id, role)
        
        # Assert
        assert result == expected_teams
        self.mock_db.query.assert_called_once_with(Team)
    
    def test_get_teams_with_member_success(self):
        """Test retrieval of teams with specific member."""
        # Arrange
        member_name = "alice"
        expected_teams = [self.sample_team]
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = expected_teams
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_teams_with_member(self.mock_db, self.project_id, member_name)
        
        # Assert
        assert result == expected_teams
        self.mock_db.query.assert_called_once_with(Team)
    
    def test_get_with_tasks_success(self):
        """Test retrieval of team with tasks."""
        # Arrange
        team_id = 1
        expected_team = self.sample_team
        mock_query = Mock()
        mock_query.filter.return_value.options.return_value.first.return_value = expected_team
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_with_tasks(self.mock_db, team_id)
        
        # Assert
        assert result == expected_team
        self.mock_db.query.assert_called_once_with(Team)
    
    def test_get_with_tasks_not_found(self):
        """Test retrieval of team with tasks when team not found."""
        # Arrange
        team_id = 999
        mock_query = Mock()
        mock_query.filter.return_value.options.return_value.first.return_value = None
        self.mock_db.query.return_value = mock_query
        
        # Act
        result = self.repository.get_with_tasks(self.mock_db, team_id)
        
        # Assert
        assert result is None
    
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
            filters = TeamSearchFilters()
            self.repository.search_teams(self.mock_db, self.project_id, filters)