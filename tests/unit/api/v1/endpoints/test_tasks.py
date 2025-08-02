"""Unit tests for task API endpoints."""
import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.api.schemas.tasks import TaskStatus
from app.domain.models.tasks import Task
from app.core.exceptions import NotFoundException, BadRequestException
from datetime import datetime

# Mock the database dependency to avoid database issues
def mock_get_db():
    return MagicMock()

# Override the dependency
from app.core.database import get_db
app.dependency_overrides[get_db] = mock_get_db

client = TestClient(app)

# Mock task data
mock_task = Task(
    id=1,
    project_id="test-project",
    description="Test task",
    assigned_to_team_id=1,
    status=TaskStatus.todo,
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow()
)

mock_task_response = {
    "id": 1,
    "project_id": "test-project",
    "description": "Test task",
    "assigned_to_team_id": 1,
    "status": "To Do",
    "created_at": "2023-01-01T00:00:00",
    "updated_at": "2023-01-01T00:00:00"
}

class TestCreateTask:
    """Test cases for creating tasks."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_create_task_success(self, mock_get_service):
        """Test successful task creation."""
        mock_service = Mock()
        mock_service.create_task.return_value = mock_task
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/v1/projects/test-project/tasks",
            json={
                "description": "Test task",
                "assigned_to_team_id": 1
            }
        )
        
        print(f"Response status: {response.status_code}")
        print(f"Response body: {response.json()}")
        assert response.status_code == 201
        mock_service.create_task.assert_called_once_with(
            "test-project", "Test task", 1
        )
    
    @patch('app.api.dependencies.get_task_service')
    def test_create_task_project_not_found(self, mock_get_service):
        """Test task creation with non-existent project."""
        mock_service = Mock()
        mock_service.create_task.side_effect = NotFoundException("Project not found")
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/v1/projects/nonexistent/tasks",
            json={
                "description": "Test task",
                "assigned_to_team_id": 1
            }
        )
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]
    
    @patch('app.api.dependencies.get_task_service')
    def test_create_task_invalid_team(self, mock_get_service):
        """Test task creation with invalid team assignment."""
        mock_service = Mock()
        mock_service.create_task.side_effect = BadRequestException("Team does not belong to project")
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/v1/projects/test-project/tasks",
            json={
                "description": "Test task",
                "assigned_to_team_id": 999
            }
        )
        
        assert response.status_code == 400
        assert "Team does not belong to project" in response.json()["detail"]
    
    @patch('app.api.dependencies.get_task_service')
    def test_create_task_empty_description(self, mock_get_service):
        """Test task creation with empty description."""
        mock_service = Mock()
        mock_service.create_task.side_effect = BadRequestException("Task description cannot be empty")
        mock_get_service.return_value = mock_service
        
        response = client.post(
            "/api/v1/projects/test-project/tasks",
            json={
                "description": "",
                "assigned_to_team_id": 1
            }
        )
        
        assert response.status_code == 400
        assert "Task description cannot be empty" in response.json()["detail"]

class TestGetTask:
    """Test cases for getting a task by ID."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_task_success(self, mock_get_service):
        """Test successful task retrieval."""
        mock_service = Mock()
        mock_service.get_task.return_value = mock_task
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/tasks/1")
        
        assert response.status_code == 200
        mock_service.get_task.assert_called_once_with(1)
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_task_not_found(self, mock_get_service):
        """Test task retrieval with non-existent task."""
        mock_service = Mock()
        mock_service.get_task.side_effect = NotFoundException("Task not found")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/tasks/999")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestGetTasksForProject:
    """Test cases for getting tasks for a project."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_tasks_for_project_success(self, mock_get_service):
        """Test successful retrieval of tasks for a project."""
        mock_service = Mock()
        mock_service.get_tasks_for_project.return_value = [mock_task]
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/projects/test-project/tasks")
        
        assert response.status_code == 200
        mock_service.get_tasks_for_project.assert_called_once_with(
            "test-project", 0, 100, None, None
        )
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_tasks_for_project_with_filters(self, mock_get_service):
        """Test retrieval of tasks for a project with filters."""
        mock_service = Mock()
        mock_service.get_tasks_for_project.return_value = [mock_task]
        mock_get_service.return_value = mock_service
        
        response = client.get(
            "/api/v1/projects/test-project/tasks?status_filter=To Do&team_id=1&skip=10&limit=50"
        )
        
        assert response.status_code == 200
        mock_service.get_tasks_for_project.assert_called_once_with(
            "test-project", 10, 50, TaskStatus.todo, 1
        )
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_tasks_for_project_not_found(self, mock_get_service):
        """Test retrieval of tasks for non-existent project."""
        mock_service = Mock()
        mock_service.get_tasks_for_project.side_effect = NotFoundException("Project not found")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/projects/nonexistent/tasks")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

class TestGetTasksForTeam:
    """Test cases for getting tasks for a team."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_tasks_for_team_success(self, mock_get_service):
        """Test successful retrieval of tasks for a team."""
        mock_service = Mock()
        mock_service.get_tasks_for_team.return_value = [mock_task]
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/teams/1/tasks")
        
        assert response.status_code == 200
        mock_service.get_tasks_for_team.assert_called_once_with(1, 0, 100, None)
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_tasks_for_team_with_status_filter(self, mock_get_service):
        """Test retrieval of tasks for a team with status filter."""
        mock_service = Mock()
        mock_service.get_tasks_for_team.return_value = [mock_task]
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/teams/1/tasks?status_filter=In Progress")
        
        assert response.status_code == 200
        mock_service.get_tasks_for_team.assert_called_once_with(
            1, 0, 100, TaskStatus.in_progress
        )
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_tasks_for_team_not_found(self, mock_get_service):
        """Test retrieval of tasks for non-existent team."""
        mock_service = Mock()
        mock_service.get_tasks_for_team.side_effect = NotFoundException("Team not found")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/teams/999/tasks")
        
        assert response.status_code == 404
        assert "Team not found" in response.json()["detail"]

class TestUpdateTask:
    """Test cases for updating tasks."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_update_task_success(self, mock_get_service):
        """Test successful task update."""
        updated_task = Task(
            id=1,
            project_id="test-project",
            description="Updated task",
            assigned_to_team_id=2,
            status=TaskStatus.in_progress,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_service = Mock()
        mock_service.update_task.return_value = updated_task
        mock_get_service.return_value = mock_service
        
        response = client.put(
            "/api/v1/tasks/1",
            json={
                "description": "Updated task",
                "assigned_to_team_id": 2,
                "status": "In Progress"
            }
        )
        
        assert response.status_code == 200
        mock_service.update_task.assert_called_once_with(
            1, "Updated task", 2, TaskStatus.in_progress
        )
    
    @patch('app.api.dependencies.get_task_service')
    def test_update_task_not_found(self, mock_get_service):
        """Test task update with non-existent task."""
        mock_service = Mock()
        mock_service.update_task.side_effect = NotFoundException("Task not found")
        mock_get_service.return_value = mock_service
        
        response = client.put(
            "/api/v1/tasks/999",
            json={
                "description": "Updated task"
            }
        )
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]
    
    @patch('app.api.dependencies.get_task_service')
    def test_update_task_no_fields(self, mock_get_service):
        """Test task update with no update fields."""
        mock_service = Mock()
        mock_service.update_task.side_effect = BadRequestException("No update fields provided")
        mock_get_service.return_value = mock_service
        
        response = client.put(
            "/api/v1/tasks/1",
            json={}
        )
        
        assert response.status_code == 400
        assert "No update fields provided" in response.json()["detail"]

class TestUpdateTaskStatus:
    """Test cases for updating task status."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_update_task_status_success(self, mock_get_service):
        """Test successful task status update."""
        updated_task = Task(
            id=1,
            project_id="test-project",
            description="Test task",
            assigned_to_team_id=1,
            status=TaskStatus.done,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_service = Mock()
        mock_service.update_task_status.return_value = updated_task
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/1/status",
            json="Done"
        )
        
        assert response.status_code == 200
        mock_service.update_task_status.assert_called_once_with(1, TaskStatus.done)
    
    @patch('app.api.dependencies.get_task_service')
    def test_update_task_status_not_found(self, mock_get_service):
        """Test task status update with non-existent task."""
        mock_service = Mock()
        mock_service.update_task_status.side_effect = NotFoundException("Task not found")
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/999/status",
            json="Done"
        )
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestAssignTaskToTeam:
    """Test cases for assigning tasks to teams."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_assign_task_to_team_success(self, mock_get_service):
        """Test successful task assignment to team."""
        assigned_task = Task(
            id=1,
            project_id="test-project",
            description="Test task",
            assigned_to_team_id=2,
            status=TaskStatus.todo,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_service = Mock()
        mock_service.assign_task_to_team.return_value = assigned_task
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/1/assign",
            json=2
        )
        
        assert response.status_code == 200
        mock_service.assign_task_to_team.assert_called_once_with(1, 2)
    
    @patch('app.api.dependencies.get_task_service')
    def test_unassign_task_from_team(self, mock_get_service):
        """Test successful task unassignment from team."""
        unassigned_task = Task(
            id=1,
            project_id="test-project",
            description="Test task",
            assigned_to_team_id=None,
            status=TaskStatus.todo,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        mock_service = Mock()
        mock_service.assign_task_to_team.return_value = unassigned_task
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/1/assign",
            json=None
        )
        
        assert response.status_code == 200
        mock_service.assign_task_to_team.assert_called_once_with(1, None)
    
    @patch('app.api.dependencies.get_task_service')
    def test_assign_task_invalid_team(self, mock_get_service):
        """Test task assignment with invalid team."""
        mock_service = Mock()
        mock_service.assign_task_to_team.side_effect = BadRequestException(
            "Team does not belong to project"
        )
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/1/assign",
            json=999
        )
        
        assert response.status_code == 400
        assert "Team does not belong to project" in response.json()["detail"]

class TestDeleteTask:
    """Test cases for deleting tasks."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_delete_task_success(self, mock_get_service):
        """Test successful task deletion."""
        mock_service = Mock()
        mock_service.delete_task.return_value = mock_task
        mock_get_service.return_value = mock_service
        
        response = client.delete("/api/v1/tasks/1")
        
        assert response.status_code == 200
        mock_service.delete_task.assert_called_once_with(1)
    
    @patch('app.api.dependencies.get_task_service')
    def test_delete_task_not_found(self, mock_get_service):
        """Test task deletion with non-existent task."""
        mock_service = Mock()
        mock_service.delete_task.side_effect = NotFoundException("Task not found")
        mock_get_service.return_value = mock_service
        
        response = client.delete("/api/v1/tasks/999")
        
        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

class TestBulkOperations:
    """Test cases for bulk operations."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_bulk_update_status_success(self, mock_get_service):
        """Test successful bulk status update."""
        updated_tasks = [mock_task, mock_task]
        
        mock_service = Mock()
        mock_service.bulk_update_status.return_value = updated_tasks
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/bulk-status-update",
            json={
                "task_ids": [1, 2],
                "status": "Done"
            }
        )
        
        assert response.status_code == 200
        mock_service.bulk_update_status.assert_called_once_with([1, 2], TaskStatus.done)
    
    @patch('app.api.dependencies.get_task_service')
    def test_bulk_assign_to_team_success(self, mock_get_service):
        """Test successful bulk team assignment."""
        updated_tasks = [mock_task, mock_task]
        
        mock_service = Mock()
        mock_service.bulk_assign_to_team.return_value = updated_tasks
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/bulk-team-assignment",
            json={
                "task_ids": [1, 2],
                "team_id": 1
            }
        )
        
        assert response.status_code == 200
        mock_service.bulk_assign_to_team.assert_called_once_with([1, 2], 1)
    
    @patch('app.api.dependencies.get_task_service')
    def test_bulk_update_empty_list(self, mock_get_service):
        """Test bulk update with empty task list."""
        mock_service = Mock()
        mock_service.bulk_update_status.side_effect = BadRequestException("No task IDs provided")
        mock_get_service.return_value = mock_service
        
        response = client.patch(
            "/api/v1/tasks/bulk-status-update",
            json={
                "task_ids": [],
                "status": "Done"
            }
        )
        
        assert response.status_code == 400
        assert "No task IDs provided" in response.json()["detail"]

class TestCountOperations:
    """Test cases for count operations."""
    
    @patch('app.api.dependencies.get_task_service')
    def test_count_tasks_for_project_success(self, mock_get_service):
        """Test successful task count for project."""
        mock_service = Mock()
        mock_service.count_tasks_for_project.return_value = 5
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/projects/test-project/tasks/count")
        
        assert response.status_code == 200
        assert response.json() == 5
        mock_service.count_tasks_for_project.assert_called_once_with("test-project")
    
    @patch('app.api.dependencies.get_task_service')
    def test_count_tasks_for_team_success(self, mock_get_service):
        """Test successful task count for team."""
        mock_service = Mock()
        mock_service.count_tasks_for_team.return_value = 3
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/teams/1/tasks/count")
        
        assert response.status_code == 200
        assert response.json() == 3
        mock_service.count_tasks_for_team.assert_called_once_with(1)
    
    @patch('app.api.dependencies.get_task_service')
    def test_get_task_status_counts_success(self, mock_get_service):
        """Test successful task status counts retrieval."""
        status_counts = {
            TaskStatus.todo: 2,
            TaskStatus.in_progress: 1,
            TaskStatus.done: 2
        }
        
        mock_service = Mock()
        mock_service.get_task_status_counts.return_value = status_counts
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/projects/test-project/tasks/status-counts")
        
        assert response.status_code == 200
        mock_service.get_task_status_counts.assert_called_once_with("test-project")
    
    @patch('app.api.dependencies.get_task_service')
    def test_count_project_not_found(self, mock_get_service):
        """Test count operations with non-existent project."""
        mock_service = Mock()
        mock_service.count_tasks_for_project.side_effect = NotFoundException("Project not found")
        mock_get_service.return_value = mock_service
        
        response = client.get("/api/v1/projects/nonexistent/tasks/count")
        
        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]