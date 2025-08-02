"""Tests for the TeamRepository.

This module contains unit tests for the TeamRepository class.
"""
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from app.repositories.team_repository import TeamRepository
from app.domain.models.teams import Team
from app.api.schemas.teams import TeamCreate, TeamUpdate
from app.core.exceptions import NotFoundException

class TestTeamRepository:
    """Test cases for the TeamRepository class."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.db = MagicMock(spec=Session)
        self.repository = TeamRepository()
        
        # Mock team instance
        self.team = MagicMock(spec=Team)
        self.team.id = 1
        self.team.project_id = "test-project"
        self.team.name = "Test Team"
        self.team.members = "John Doe, Jane Smith"

    def test_get_by_name_existing(self):
        """Test getting a team by name when it exists."""
        # Arrange
        self.db.query.return_value.filter.return_value.filter.return_value.first.return_value = self.team
        
        # Act
        result = self.repository.get_by_name(self.db, project_id="test-project", name="Test Team")
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        assert result == self.team

    def test_get_by_name_non_existing(self):
        """Test getting a team by name when it doesn't exist."""
        # Arrange
        self.db.query.return_value.filter.return_value.filter.return_value.first.return_value = None
        
        # Act
        result = self.repository.get_by_name(self.db, project_id="test-project", name="Non-existing Team")
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        assert result is None

    def test_get_by_project(self):
        """Test getting teams by project."""
        # Arrange
        teams = [self.team, MagicMock(spec=Team)]
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.offset.return_value.limit.return_value.all.return_value = teams
        
        # Act
        result = self.repository.get_by_project(self.db, project_id="test-project", skip=0, limit=10)
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.offset.assert_called_once_with(0)
        query_mock.filter.return_value.offset.return_value.limit.assert_called_once_with(10)
        assert result == teams

    def test_get_with_tasks(self):
        """Test getting a team with its tasks."""
        # Arrange
        query_mock = self.db.query.return_value
        query_mock.options.return_value.filter.return_value.first.return_value = self.team
        
        # Act
        result = self.repository.get_with_tasks(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        query_mock.options.assert_called_once()
        assert result == self.team

    def test_search_teams(self):
        """Test searching teams."""
        # Arrange
        teams = [self.team]
        query_mock = self.db.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.filter.return_value.offset.return_value.limit.return_value.all.return_value = teams
        
        # Act
        result = self.repository.search_teams(
            self.db, 
            project_id="test-project", 
            query="test", 
            skip=0, 
            limit=10
        )
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        assert result == teams

    def test_count_by_project(self):
        """Test counting teams by project."""
        # Arrange
        query_mock = self.db.query.return_value
        query_mock.filter.return_value.count.return_value = 5
        
        # Act
        result = self.repository.count_by_project(self.db, project_id="test-project")
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        query_mock.filter.assert_called_once()
        query_mock.filter.return_value.count.assert_called_once()
        assert result == 5

    def test_create_team(self):
        """Test creating a team."""
        # Arrange
        create_data = TeamCreate(
            project_id="test-project",
            name="New Team",
            members="Alice, Bob"
        )
        
        with patch.object(Team, '__init__', return_value=None) as mock_init:
            mock_instance = MagicMock(spec=Team)
            
            with patch.object(Team, '__new__', return_value=mock_instance):
                # Act
                result = self.repository.create(self.db, obj_in=create_data)
                
                # Assert
                self.db.add.assert_called_once_with(mock_instance)
                self.db.commit.assert_called_once()
                self.db.refresh.assert_called_once_with(mock_instance)
                assert result == mock_instance

    def test_update_team(self):
        """Test updating a team."""
        # Arrange
        update_data = TeamUpdate(name="Updated Team", members="Alice, Bob, Charlie")
        
        # Act
        result = self.repository.update(self.db, db_obj=self.team, obj_in=update_data)
        
        # Assert
        assert self.team.name == "Updated Team"
        assert self.team.members == "Alice, Bob, Charlie"
        self.db.add.assert_called_once_with(self.team)
        self.db.commit.assert_called_once()
        self.db.refresh.assert_called_once_with(self.team)
        assert result == self.team

    def test_delete_team(self):
        """Test deleting a team."""
        # Arrange
        self.db.query.return_value.filter.return_value.first.return_value = self.team
        
        # Act
        result = self.repository.delete(self.db, id=1)
        
        # Assert
        self.db.query.assert_called_once_with(Team)
        self.db.delete.assert_called_once_with(self.team)
        self.db.commit.assert_called_once()
        assert result == self.team