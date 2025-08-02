"""Unit tests for TaskService."""
import pytest
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from app.services.tasks import TaskService
from app.domain.models.tasks import Task, TaskStatus
from app.domain.models.teams import Team
from app.domain.models.projects import Project
from app.api.schemas.tasks import TaskCreate, TaskUpdate
from app.core.exceptions import NotFoundException, BadRequestException


class TestTaskService:
    """Test cases for TaskService."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.db = Mock(spec=Session)
        self.service = TaskService(self.db)
        
        # Mock repositories
        self.service.task_repository = Mock()
        self.service.project_repository = Mock()
        self.service.team_repository = Mock()
        
        # Sample data
        self.project = Project(
            id="test-project",
            name="Test Project",
            description="Test Description"
        )
        
        self.team = Team(
            id=1,
            project_id="test-project",
            name="Test Team",
            members="John, Jane"
        )
        
        self.task = Task(
            id=1,
            project_id="test-project",
            description="Test Task",
            assigned_to_team_id=1,
            status=TaskStatus.todo
        )
    
    def test_create_task_success(self):
        """Test successful task creation."""
        # Arrange
        self.service.project_repository.get_or_404.return_value = self.project
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.create.return_value = self.task
        
        # Act
        result = self.service.create_task(
            project_id="test-project",
            description="Test Task",
            assigned_to_team_id=1
        )
        
        # Assert
        assert result == self.task
        self.service.project_repository.get_or_404.assert_called_once_with(self.db, "test-project")
        self.service.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.create.assert_called_once()
    
    def test_create_task_without_team(self):
        """Test task creation without team assignment."""
        # Arrange
        self.service.project_repository.get_or_404.return_value = self.project
        task_without_team = Task(
            id=1,
            project_id="test-project",
            description="Test Task",
            assigned_to_team_id=None,
            status=TaskStatus.todo
        )
        self.service.task_repository.create.return_value = task_without_team
        
        # Act
        result = self.service.create_task(
            project_id="test-project",
            description="Test Task"
        )
        
        # Assert
        assert result == task_without_team
        self.service.project_repository.get_or_404.assert_called_once_with(self.db, "test-project")
        self.service.team_repository.get_or_404.assert_not_called()
        self.service.task_repository.create.assert_called_once()
    
    def test_create_task_empty_description(self):
        """Test task creation with empty description."""
        # Act & Assert
        with pytest.raises(BadRequestException, match="Task description cannot be empty"):
            self.service.create_task(
                project_id="test-project",
                description=""
            )
    
    def test_create_task_project_not_found(self):
        """Test task creation with non-existent project."""
        # Arrange
        self.service.project_repository.get_or_404.side_effect = NotFoundException(
            "Project not found", resource_type="Project"
        )
        
        # Act & Assert
        with pytest.raises(NotFoundException):
            self.service.create_task(
                project_id="non-existent",
                description="Test Task"
            )
    
    def test_create_task_team_wrong_project(self):
        """Test task creation with team from different project."""
        # Arrange
        self.service.project_repository.get_or_404.return_value = self.project
        wrong_team = Team(
            id=2,
            project_id="other-project",
            name="Other Team",
            members="Bob"
        )
        self.service.team_repository.get_or_404.return_value = wrong_team
        
        # Act & Assert
        with pytest.raises(BadRequestException, match="does not belong to project"):
            self.service.create_task(
                project_id="test-project",
                description="Test Task",
                assigned_to_team_id=2
            )
    
    def test_get_task_success(self):
        """Test successful task retrieval."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        
        # Act
        result = self.service.get_task(1)
        
        # Assert
        assert result == self.task
        self.service.task_repository.get_or_404.assert_called_once_with(self.db, 1)
    
    def test_get_tasks_for_project_no_filters(self):
        """Test getting tasks for project without filters."""
        # Arrange
        tasks = [self.task]
        self.service.project_repository.get_or_404.return_value = self.project
        self.service.task_repository.get_by_project.return_value = tasks
        
        # Act
        result = self.service.get_tasks_for_project("test-project")
        
        # Assert
        assert result == tasks
        self.service.project_repository.get_or_404.assert_called_once_with(self.db, "test-project")
        self.service.task_repository.get_by_project.assert_called_once_with(
            self.db, project_id="test-project", skip=0, limit=100
        )
    
    def test_get_tasks_for_project_with_status_filter(self):
        """Test getting tasks for project with status filter."""
        # Arrange
        tasks = [self.task]
        self.service.project_repository.get_or_404.return_value = self.project
        self.service.task_repository.get_by_status.return_value = tasks
        
        # Act
        result = self.service.get_tasks_for_project(
            "test-project", 
            status=TaskStatus.todo
        )
        
        # Assert
        assert result == tasks
        self.service.task_repository.get_by_status.assert_called_once_with(
            self.db, project_id="test-project", status=TaskStatus.todo, skip=0, limit=100
        )
    
    def test_get_tasks_for_project_with_team_filter(self):
        """Test getting tasks for project with team filter."""
        # Arrange
        tasks = [self.task]
        self.service.project_repository.get_or_404.return_value = self.project
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.get_by_team.return_value = tasks
        
        # Act
        result = self.service.get_tasks_for_project(
            "test-project", 
            team_id=1
        )
        
        # Assert
        assert result == tasks
        self.service.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.get_by_team.assert_called_once_with(
            self.db, team_id=1, skip=0, limit=100
        )
    
    def test_get_tasks_for_project_with_both_filters(self):
        """Test getting tasks for project with both status and team filters."""
        # Arrange
        tasks = [self.task]
        self.service.project_repository.get_or_404.return_value = self.project
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.get_by_team_and_status.return_value = tasks
        
        # Act
        result = self.service.get_tasks_for_project(
            "test-project", 
            status=TaskStatus.todo,
            team_id=1
        )
        
        # Assert
        assert result == tasks
        self.service.task_repository.get_by_team_and_status.assert_called_once_with(
            self.db, team_id=1, status=TaskStatus.todo, skip=0, limit=100
        )
    
    def test_get_tasks_for_team_success(self):
        """Test getting tasks for team."""
        # Arrange
        tasks = [self.task]
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.get_by_team.return_value = tasks
        
        # Act
        result = self.service.get_tasks_for_team(1)
        
        # Assert
        assert result == tasks
        self.service.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.get_by_team.assert_called_once_with(
            self.db, team_id=1, skip=0, limit=100
        )
    
    def test_update_task_success(self):
        """Test successful task update."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        self.service.team_repository.get_or_404.return_value = self.team
        updated_task = Task(
            id=1,
            project_id="test-project",
            description="Updated Task",
            assigned_to_team_id=1,
            status=TaskStatus.in_progress
        )
        self.service.task_repository.update.return_value = updated_task
        
        # Act
        result = self.service.update_task(
            task_id=1,
            description="Updated Task",
            status=TaskStatus.in_progress
        )
        
        # Assert
        assert result == updated_task
        self.service.task_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.update.assert_called_once()
    
    def test_update_task_no_fields(self):
        """Test task update with no fields provided."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        
        # Act & Assert
        with pytest.raises(BadRequestException, match="No update fields provided"):
            self.service.update_task(task_id=1)
    
    def test_update_task_empty_description(self):
        """Test task update with empty description."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        
        # Act & Assert
        with pytest.raises(BadRequestException, match="Task description cannot be empty"):
            self.service.update_task(task_id=1, description="")
    
    def test_update_task_status_success(self):
        """Test successful task status update."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        updated_task = Task(
            id=1,
            project_id="test-project",
            description="Test Task",
            assigned_to_team_id=1,
            status=TaskStatus.done
        )
        self.service.task_repository.update_status.return_value = updated_task
        
        # Act
        result = self.service.update_task_status(1, TaskStatus.done)
        
        # Assert
        assert result == updated_task
        self.service.task_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.update_status.assert_called_once_with(
            self.db, id=1, status=TaskStatus.done
        )
    
    def test_assign_task_to_team_success(self):
        """Test successful task assignment to team."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.assign_to_team.return_value = self.task
        
        # Act
        result = self.service.assign_task_to_team(1, 1)
        
        # Assert
        assert result == self.task
        self.service.task_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.assign_to_team.assert_called_once_with(
            self.db, id=1, team_id=1
        )
    
    def test_assign_task_to_team_unassign(self):
        """Test unassigning task from team."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        unassigned_task = Task(
            id=1,
            project_id="test-project",
            description="Test Task",
            assigned_to_team_id=None,
            status=TaskStatus.todo
        )
        self.service.task_repository.assign_to_team.return_value = unassigned_task
        
        # Act
        result = self.service.assign_task_to_team(1, None)
        
        # Assert
        assert result == unassigned_task
        self.service.task_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.team_repository.get_or_404.assert_not_called()
        self.service.task_repository.assign_to_team.assert_called_once_with(
            self.db, id=1, team_id=None
        )
    
    def test_delete_task_success(self):
        """Test successful task deletion."""
        # Arrange
        self.service.task_repository.get_or_404.return_value = self.task
        self.service.task_repository.delete.return_value = self.task
        
        # Act
        result = self.service.delete_task(1)
        
        # Assert
        assert result == self.task
        self.service.task_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.delete.assert_called_once_with(self.db, id=1)
    
    def test_bulk_update_status_success(self):
        """Test successful bulk status update."""
        # Arrange
        task_ids = [1, 2, 3]
        tasks = [self.task] * 3
        self.service.task_repository.get_or_404.side_effect = tasks
        self.service.task_repository.bulk_update_status.return_value = tasks
        
        # Act
        result = self.service.bulk_update_status(task_ids, TaskStatus.done)
        
        # Assert
        assert result == tasks
        assert self.service.task_repository.get_or_404.call_count == 3
        self.service.task_repository.bulk_update_status.assert_called_once_with(
            self.db, ids=task_ids, status=TaskStatus.done
        )
    
    def test_bulk_update_status_empty_list(self):
        """Test bulk status update with empty list."""
        # Act & Assert
        with pytest.raises(BadRequestException, match="No task IDs provided"):
            self.service.bulk_update_status([], TaskStatus.done)
    
    def test_bulk_assign_to_team_success(self):
        """Test successful bulk team assignment."""
        # Arrange
        task_ids = [1, 2, 3]
        tasks = [self.task] * 3
        self.service.task_repository.get_or_404.side_effect = tasks
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.bulk_assign_to_team.return_value = tasks
        
        # Act
        result = self.service.bulk_assign_to_team(task_ids, 1)
        
        # Assert
        assert result == tasks
        assert self.service.task_repository.get_or_404.call_count == 3
        self.service.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.bulk_assign_to_team.assert_called_once_with(
            self.db, ids=task_ids, team_id=1
        )
    
    def test_count_tasks_for_project_success(self):
        """Test counting tasks for project."""
        # Arrange
        self.service.project_repository.get_or_404.return_value = self.project
        self.service.task_repository.count_by_project.return_value = 5
        
        # Act
        result = self.service.count_tasks_for_project("test-project")
        
        # Assert
        assert result == 5
        self.service.project_repository.get_or_404.assert_called_once_with(self.db, "test-project")
        self.service.task_repository.count_by_project.assert_called_once_with(
            self.db, project_id="test-project"
        )
    
    def test_count_tasks_for_team_success(self):
        """Test counting tasks for team."""
        # Arrange
        self.service.team_repository.get_or_404.return_value = self.team
        self.service.task_repository.count_by_team.return_value = 3
        
        # Act
        result = self.service.count_tasks_for_team(1)
        
        # Assert
        assert result == 3
        self.service.team_repository.get_or_404.assert_called_once_with(self.db, 1)
        self.service.task_repository.count_by_team.assert_called_once_with(
            self.db, team_id=1
        )
    
    def test_get_task_status_counts_success(self):
        """Test getting task status counts for project."""
        # Arrange
        self.service.project_repository.get_or_404.return_value = self.project
        status_counts = {
            TaskStatus.todo: 2,
            TaskStatus.in_progress: 1,
            TaskStatus.done: 3
        }
        self.service.task_repository.get_status_counts.return_value = status_counts
        
        # Act
        result = self.service.get_task_status_counts("test-project")
        
        # Assert
        assert result == status_counts
        self.service.project_repository.get_or_404.assert_called_once_with(self.db, "test-project")
        self.service.task_repository.get_status_counts.assert_called_once_with(
            self.db, project_id="test-project"
        )