"""Unit tests for TeamService."""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.team_service import TeamService
from app.repositories.team_repository import TeamRepository
from app.repositories.project_repository import ProjectRepository
from app.domain.models.teams import Team
from app.domain.models.projects import Project
from app.api.schemas.teams import TeamCreate, TeamUpdate, TeamUpsert, TeamSearchFilters
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException


class TestTeamService:
    """Test cases for TeamService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_team_repo = Mock(spec=TeamRepository)
        self.mock_project_repo = Mock(spec=ProjectRepository)
        self.service = TeamService(self.mock_team_repo, self.mock_project_repo)
        self.mock_db = Mock(spec=Session)
        self.project_id = "test-project-123"
        
        # Sample data
        self.sample_project = Project(
            id=self.project_id,
            name="Test Project",
            description="A test project"
        )
        
        self.sample_team = Team(
            id=1,
            project_id=self.project_id,
            name="Backend Team",
            role="Development Team",
            members=["Alice Johnson", "Bob Smith"],
            responsibilities=["API Development", "Database Design"]
        )
    
    def test_create_team_success(self):
        """Test successful team creation."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="New Team",
            role="Development Team",
            members=["Alice", "Bob"],
            responsibilities=["Coding", "Testing"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project_and_name.return_value = None
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": True,
            "invalid_members": [],
            "duplicate_members": []
        }
        self.mock_team_repo.create.return_value = self.sample_team
        
        # Act
        result = self.service.create_team(self.mock_db, team_data)
        
        # Assert
        assert result.id == self.sample_team.id
        assert result.name == self.sample_team.name
        self.mock_project_repo.get.assert_called_once_with(self.mock_db, self.project_id)
        self.mock_team_repo.create.assert_called_once()
    
    def test_create_team_project_not_found(self):
        """Test team creation when project doesn't exist."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="New Team",
            role="Development Team"
        )
        
        self.mock_project_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            self.service.create_team(self.mock_db, team_data)
        
        assert "Project with id" in str(exc_info.value)
        self.mock_team_repo.create.assert_not_called()
    
    def test_create_team_duplicate_name(self):
        """Test team creation with duplicate name."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="Existing Team",
            role="Development Team"
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project_and_name.return_value = self.sample_team
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_team(self.mock_db, team_data)
        
        assert "already exists" in str(exc_info.value)
        self.mock_team_repo.create.assert_not_called()
    
    def test_create_team_invalid_members(self):
        """Test team creation with invalid members."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="New Team",
            role="Development Team",
            members=["Alice", "", "Bob"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project_and_name.return_value = None
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": False,
            "invalid_members": [""],
            "duplicate_members": []
        }
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_team(self.mock_db, team_data)
        
        assert "Member validation failed" in str(exc_info.value)
        self.mock_team_repo.create.assert_not_called()
    
    def test_create_team_duplicate_members(self):
        """Test team creation with duplicate members."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="New Team",
            role="Development Team",
            members=["Alice", "Bob", "Alice"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project_and_name.return_value = None
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": False,
            "invalid_members": [],
            "duplicate_members": ["Alice"]
        }
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_team(self.mock_db, team_data)
        
        assert "Duplicate members" in str(exc_info.value)
        self.mock_team_repo.create.assert_not_called()
    
    def test_create_team_empty_responsibilities(self):
        """Test team creation with empty responsibilities."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="New Team",
            role="Development Team",
            members=["Alice"],
            responsibilities=["Coding", "", "Testing"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project_and_name.return_value = None
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": True,
            "invalid_members": [],
            "duplicate_members": []
        }
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.create_team(self.mock_db, team_data)
        
        assert "Responsibilities cannot be empty" in str(exc_info.value)
        self.mock_team_repo.create.assert_not_called()
    
    def test_get_team_success(self):
        """Test successful team retrieval."""
        # Arrange
        team_id = 1
        self.mock_team_repo.get_or_404.return_value = self.sample_team
        
        # Act
        result = self.service.get_team(self.mock_db, team_id)
        
        # Assert
        assert result.id == self.sample_team.id
        assert result.name == self.sample_team.name
        self.mock_team_repo.get_or_404.assert_called_once_with(self.mock_db, team_id)
    
    def test_get_team_not_found(self):
        """Test team retrieval when team doesn't exist."""
        # Arrange
        team_id = 999
        self.mock_team_repo.get_or_404.side_effect = NotFoundException("Team not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.get_team(self.mock_db, team_id)
    
    def test_upsert_team_create_new(self):
        """Test upserting a team that doesn't exist (create)."""
        # Arrange
        team_data = TeamUpsert(
            project_id=self.project_id,
            name="New Team",
            role="Development Team",
            members=["Alice", "Bob"],
            responsibilities=["Coding", "Testing"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": True,
            "invalid_members": [],
            "duplicate_members": []
        }
        self.mock_team_repo.upsert_team.return_value = self.sample_team
        
        # Act
        result = self.service.upsert_team(self.mock_db, team_data)
        
        # Assert
        assert result.id == self.sample_team.id
        self.mock_team_repo.upsert_team.assert_called_once()
    
    def test_upsert_team_update_existing(self):
        """Test upserting a team that exists (update)."""
        # Arrange
        team_data = TeamUpsert(
            project_id=self.project_id,
            name="Existing Team",
            role="Senior Development Team",
            members=["Alice", "Bob", "Charlie"],
            responsibilities=["Architecture", "Code Review"]
        )
        
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": True,
            "invalid_members": [],
            "duplicate_members": []
        }
        self.mock_team_repo.upsert_team.return_value = self.sample_team
        
        # Act
        result = self.service.upsert_team(self.mock_db, team_data)
        
        # Assert
        assert result.id == self.sample_team.id
        self.mock_team_repo.upsert_team.assert_called_once()
    
    def test_update_team_success(self):
        """Test successful team update."""
        # Arrange
        team_id = 1
        team_data = TeamUpdate(
            name="Updated Team",
            role="Senior Development Team",
            members=["Alice", "Bob", "Charlie"],
            responsibilities=["Architecture", "Mentoring"]
        )
        
        self.mock_team_repo.get_or_404.return_value = self.sample_team
        self.mock_team_repo.get_by_project_and_name.return_value = None
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": True,
            "invalid_members": [],
            "duplicate_members": []
        }
        self.mock_team_repo.update_by_id.return_value = self.sample_team
        
        # Act
        result = self.service.update_team(self.mock_db, team_id, team_data)
        
        # Assert
        assert result.id == self.sample_team.id
        self.mock_team_repo.update_by_id.assert_called_once()
    
    def test_update_team_duplicate_name(self):
        """Test team update with duplicate name."""
        # Arrange
        team_id = 1
        team_data = TeamUpdate(name="Duplicate Name")
        
        existing_team = Mock()
        existing_team.name = "Original Name"
        existing_team.project_id = self.project_id
        
        duplicate_team = Mock()
        duplicate_team.id = 2
        
        self.mock_team_repo.get_or_404.return_value = existing_team
        self.mock_team_repo.get_by_project_and_name.return_value = duplicate_team
        
        # Act & Assert
        with pytest.raises(BadRequestException) as exc_info:
            self.service.update_team(self.mock_db, team_id, team_data)
        
        assert "already exists" in str(exc_info.value)
        self.mock_team_repo.update_by_id.assert_not_called()
    
    def test_delete_team_success(self):
        """Test successful team deletion."""
        # Arrange
        team_id = 1
        self.mock_team_repo.get_or_404.return_value = self.sample_team
        
        # Act
        result = self.service.delete_team(self.mock_db, team_id)
        
        # Assert
        assert result is True
        self.mock_team_repo.delete.assert_called_once_with(self.mock_db, id=team_id)
    
    def test_delete_team_not_found(self):
        """Test team deletion when team doesn't exist."""
        # Arrange
        team_id = 999
        self.mock_team_repo.get_or_404.side_effect = NotFoundException("Team not found")
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.delete_team(self.mock_db, team_id)
        
        self.mock_team_repo.delete.assert_not_called()
    
    def test_list_teams_success(self):
        """Test successful team listing."""
        # Arrange
        teams = [self.sample_team]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project.return_value = teams
        
        # Act
        result = self.service.list_teams(self.mock_db, self.project_id)
        
        # Assert
        assert len(result) == 1
        assert result[0].id == self.sample_team.id
        self.mock_team_repo.get_by_project.assert_called_once()
    
    def test_list_teams_with_filters(self):
        """Test team listing with filters."""
        # Arrange
        filters = TeamSearchFilters(name="backend", role="development")
        teams = [self.sample_team]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.search_teams.return_value = teams
        
        # Act
        result = self.service.list_teams(self.mock_db, self.project_id, filters)
        
        # Assert
        assert len(result) == 1
        self.mock_team_repo.search_teams.assert_called_once()
    
    def test_list_teams_project_not_found(self):
        """Test team listing when project doesn't exist."""
        # Arrange
        self.mock_project_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.list_teams(self.mock_db, self.project_id)
    
    def test_get_teams_by_role_success(self):
        """Test successful retrieval of teams by role."""
        # Arrange
        role = "development"
        teams = [self.sample_team]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_teams_by_role.return_value = teams
        
        # Act
        result = self.service.get_teams_by_role(self.mock_db, self.project_id, role)
        
        # Assert
        assert len(result) == 1
        assert result[0].role == self.sample_team.role
        self.mock_team_repo.get_teams_by_role.assert_called_once()
    
    def test_get_teams_with_member_success(self):
        """Test successful retrieval of teams with specific member."""
        # Arrange
        member_name = "alice"
        teams = [self.sample_team]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_teams_with_member.return_value = teams
        
        # Act
        result = self.service.get_teams_with_member(self.mock_db, self.project_id, member_name)
        
        # Assert
        assert len(result) == 1
        assert "Alice Johnson" in result[0].members
        self.mock_team_repo.get_teams_with_member.assert_called_once()
    
    def test_count_teams_success(self):
        """Test successful team counting."""
        # Arrange
        expected_count = 3
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.count_by_project.return_value = expected_count
        
        # Act
        result = self.service.count_teams(self.mock_db, self.project_id)
        
        # Assert
        assert result == expected_count
        self.mock_team_repo.count_by_project.assert_called_once()
    
    def test_count_teams_with_filters(self):
        """Test team counting with filters."""
        # Arrange
        filters = TeamSearchFilters(role="development")
        expected_count = 2
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.count_by_project.return_value = expected_count
        
        # Act
        result = self.service.count_teams(self.mock_db, self.project_id, filters)
        
        # Assert
        assert result == expected_count
        self.mock_team_repo.count_by_project.assert_called_once_with(self.mock_db, self.project_id, filters)
    
    def test_validate_team_members_success(self):
        """Test successful member validation."""
        # Arrange
        members = ["Alice", "Bob", "Charlie"]
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": True,
            "invalid_members": [],
            "duplicate_members": []
        }
        
        # Act
        result = self.service.validate_team_members(members)
        
        # Assert
        assert result["valid"] is True
        assert result["invalid_members"] == []
        assert result["duplicate_members"] == []
    
    def test_validate_team_members_invalid(self):
        """Test member validation with invalid members."""
        # Arrange
        members = ["Alice", "", "Bob", "Alice"]
        self.mock_team_repo.validate_member_names.return_value = {
            "valid": False,
            "invalid_members": [""],
            "duplicate_members": ["Alice"]
        }
        
        # Act
        result = self.service.validate_team_members(members)
        
        # Assert
        assert result["valid"] is False
        assert "" in result["invalid_members"]
        assert "Alice" in result["duplicate_members"]
    
    def test_analyze_team_responsibilities_success(self):
        """Test successful team responsibility analysis."""
        # Arrange
        team1 = Mock()
        team1.name = "Backend Team"
        team1.responsibilities = ["API Development", "Database Design"]
        
        team2 = Mock()
        team2.name = "Frontend Team"
        team2.responsibilities = ["UI Development", "API Development"]  # Overlap with Backend
        
        teams = [team1, team2]
        self.mock_project_repo.get.return_value = self.sample_project
        self.mock_team_repo.get_by_project.return_value = teams
        
        # Act
        result = self.service.analyze_team_responsibilities(self.mock_db, self.project_id)
        
        # Assert
        assert result["total_teams"] == 2
        assert result["teams_with_responsibilities"] == 2
        assert result["unique_responsibilities"] == 3  # API Development, Database Design, UI Development
        assert result["total_responsibility_assignments"] == 4
        assert "API Development" in result["overlapping_responsibilities"]
        assert result["overlapping_responsibilities"]["API Development"] == 2
    
    def test_analyze_team_responsibilities_project_not_found(self):
        """Test responsibility analysis when project doesn't exist."""
        # Arrange
        self.mock_project_repo.get.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.analyze_team_responsibilities(self.mock_db, self.project_id)
    
    def test_to_response_conversion(self):
        """Test conversion from Team model to TeamResponse."""
        # Act
        result = self.service._to_response(self.sample_team)
        
        # Assert
        assert result.id == self.sample_team.id
        assert result.project_id == self.sample_team.project_id
        assert result.name == self.sample_team.name
        assert result.role == self.sample_team.role
        assert result.members == self.sample_team.members
        assert result.responsibilities == self.sample_team.responsibilities
        assert result.created_at == self.sample_team.created_at
        assert result.updated_at == self.sample_team.updated_at
    
    def test_database_error_handling(self):
        """Test general database error handling."""
        # Arrange
        team_data = TeamCreate(
            project_id=self.project_id,
            name="Test Team",
            role="Development Team"
        )
        
        self.mock_project_repo.get.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(DatabaseException):
            self.service.create_team(self.mock_db, team_data)