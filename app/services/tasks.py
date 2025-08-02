"""Task service implementation.

This module provides a service for managing tasks.
It follows the service pattern and provides a clean interface for task operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.task_repository import task_repository
from app.repositories.project_repository import project_repository
from app.repositories.team_repository import team_repository
from app.domain.models.tasks import Task, TaskStatus
from app.api.schemas.tasks import TaskCreate, TaskUpdate, TaskResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException

class TaskService:
    """Task service class.
    
    This class provides business logic for managing tasks.
    """
    
    def __init__(self, db: Session):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.task_repository = task_repository
        self.project_repository = project_repository
        self.team_repository = team_repository
    
    def create_task(
        self, 
        project_id: str, 
        description: str, 
        assigned_to_team_id: Optional[int] = None
    ) -> Task:
        """Create a new task.
        
        Args:
            project_id: The ID of the project.
            description: The description of the task.
            assigned_to_team_id: The ID of the team to assign the task to.
            
        Returns:
            The created task.
            
        Raises:
            NotFoundException: If the project or team is not found.
            BadRequestException: If the description is empty.
        """
        # Validate description
        if not description or not description.strip():
            raise BadRequestException("Task description cannot be empty")
        
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Check if team exists and belongs to the project (if team is specified)
        if assigned_to_team_id is not None:
            team = self.team_repository.get_or_404(self.db, assigned_to_team_id)
            if team.project_id != project_id:
                raise BadRequestException(
                    f"Team {assigned_to_team_id} does not belong to project {project_id}"
                )
        
        # Create task
        task_data = TaskCreate(
            project_id=project_id,
            description=description.strip(),
            assigned_to_team_id=assigned_to_team_id
        )
        
        return self.task_repository.create(self.db, obj_in=task_data)
    
    def get_task(self, task_id: int) -> Task:
        """Get a task by ID.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            The task with team assignment information.
            
        Raises:
            NotFoundException: If the task is not found.
        """
        return self.task_repository.get_or_404(self.db, task_id)
    
    def get_tasks_for_project(
        self, 
        project_id: str, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[TaskStatus] = None,
        team_id: Optional[int] = None
    ) -> List[Task]:
        """Get all tasks for a project with optional filtering.
        
        Args:
            project_id: The ID of the project.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            status: Optional status filter.
            team_id: Optional team filter.
            
        Returns:
            A list of tasks for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Apply filters
        if status is not None and team_id is not None:
            # Filter by both status and team
            team = self.team_repository.get_or_404(self.db, team_id)
            if team.project_id != project_id:
                raise BadRequestException(
                    f"Team {team_id} does not belong to project {project_id}"
                )
            return self.task_repository.get_by_team_and_status(
                self.db, team_id=team_id, status=status, skip=skip, limit=limit
            )
        elif status is not None:
            # Filter by status only
            return self.task_repository.get_by_status(
                self.db, project_id=project_id, status=status, skip=skip, limit=limit
            )
        elif team_id is not None:
            # Filter by team only
            team = self.team_repository.get_or_404(self.db, team_id)
            if team.project_id != project_id:
                raise BadRequestException(
                    f"Team {team_id} does not belong to project {project_id}"
                )
            return self.task_repository.get_by_team(
                self.db, team_id=team_id, skip=skip, limit=limit
            )
        else:
            # No filters
            return self.task_repository.get_by_project(
                self.db, project_id=project_id, skip=skip, limit=limit
            )
    
    def get_tasks_for_team(
        self, 
        team_id: int, 
        skip: int = 0, 
        limit: int = 100,
        status: Optional[TaskStatus] = None
    ) -> List[Task]:
        """Get all tasks assigned to a team.
        
        Args:
            team_id: The ID of the team.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            status: Optional status filter.
            
        Returns:
            A list of tasks assigned to the team.
            
        Raises:
            NotFoundException: If the team is not found.
        """
        # Check if team exists
        team = self.team_repository.get_or_404(self.db, team_id)
        
        if status is not None:
            return self.task_repository.get_by_team_and_status(
                self.db, team_id=team_id, status=status, skip=skip, limit=limit
            )
        else:
            return self.task_repository.get_by_team(
                self.db, team_id=team_id, skip=skip, limit=limit
            )
    
    def update_task(
        self, 
        task_id: int, 
        description: Optional[str] = None,
        assigned_to_team_id: Optional[int] = None,
        status: Optional[TaskStatus] = None
    ) -> Task:
        """Update a task.
        
        Args:
            task_id: The ID of the task.
            description: The new description of the task.
            assigned_to_team_id: The new team assignment (None to unassign).
            status: The new status of the task.
            
        Returns:
            The updated task.
            
        Raises:
            NotFoundException: If the task or team is not found.
            BadRequestException: If no update fields are provided or validation fails.
        """
        # Check if task exists
        task = self.task_repository.get_or_404(self.db, task_id)
        
        # Check if update fields are provided
        if description is None and assigned_to_team_id is None and status is None:
            raise BadRequestException("No update fields provided")
        
        # Validate description if provided
        if description is not None and (not description or not description.strip()):
            raise BadRequestException("Task description cannot be empty")
        
        # Validate team assignment if provided
        if assigned_to_team_id is not None:
            team = self.team_repository.get_or_404(self.db, assigned_to_team_id)
            if team.project_id != task.project_id:
                raise BadRequestException(
                    f"Team {assigned_to_team_id} does not belong to project {task.project_id}"
                )
        
        # Create update data
        update_data = TaskUpdate(
            description=description.strip() if description is not None else task.description,
            assigned_to_team_id=assigned_to_team_id if assigned_to_team_id is not None else task.assigned_to_team_id,
            status=status if status is not None else task.status
        )
        
        return self.task_repository.update(self.db, db_obj=task, obj_in=update_data)
    
    def update_task_status(self, task_id: int, status: TaskStatus) -> Task:
        """Update the status of a task.
        
        Args:
            task_id: The ID of the task.
            status: The new status.
            
        Returns:
            The updated task.
            
        Raises:
            NotFoundException: If the task is not found.
        """
        # Check if task exists
        task = self.task_repository.get_or_404(self.db, task_id)
        
        return self.task_repository.update_status(self.db, id=task_id, status=status)
    
    def assign_task_to_team(self, task_id: int, team_id: Optional[int]) -> Task:
        """Assign a task to a team.
        
        Args:
            task_id: The ID of the task.
            team_id: The ID of the team, or None to unassign.
            
        Returns:
            The updated task.
            
        Raises:
            NotFoundException: If the task or team is not found.
            BadRequestException: If the team doesn't belong to the task's project.
        """
        # Check if task exists
        task = self.task_repository.get_or_404(self.db, task_id)
        
        # Validate team assignment if provided
        if team_id is not None:
            team = self.team_repository.get_or_404(self.db, team_id)
            if team.project_id != task.project_id:
                raise BadRequestException(
                    f"Team {team_id} does not belong to project {task.project_id}"
                )
        
        return self.task_repository.assign_to_team(self.db, id=task_id, team_id=team_id)
    
    def delete_task(self, task_id: int) -> Task:
        """Delete a task.
        
        Args:
            task_id: The ID of the task.
            
        Returns:
            The deleted task.
            
        Raises:
            NotFoundException: If the task is not found.
        """
        # Check if task exists
        task = self.task_repository.get_or_404(self.db, task_id)
        
        return self.task_repository.delete(self.db, id=task_id)
    
    def bulk_update_status(self, task_ids: List[int], status: TaskStatus) -> List[Task]:
        """Update the status of multiple tasks.
        
        Args:
            task_ids: The IDs of the tasks.
            status: The new status.
            
        Returns:
            The updated tasks.
            
        Raises:
            BadRequestException: If no task IDs are provided.
        """
        if not task_ids:
            raise BadRequestException("No task IDs provided")
        
        # Validate that all tasks exist (this will raise NotFoundException if any don't exist)
        for task_id in task_ids:
            self.task_repository.get_or_404(self.db, task_id)
        
        return self.task_repository.bulk_update_status(self.db, ids=task_ids, status=status)
    
    def bulk_assign_to_team(self, task_ids: List[int], team_id: Optional[int]) -> List[Task]:
        """Assign multiple tasks to a team.
        
        Args:
            task_ids: The IDs of the tasks.
            team_id: The ID of the team, or None to unassign.
            
        Returns:
            The updated tasks.
            
        Raises:
            BadRequestException: If no task IDs are provided or team validation fails.
            NotFoundException: If any task or the team is not found.
        """
        if not task_ids:
            raise BadRequestException("No task IDs provided")
        
        # Validate that all tasks exist and get their project IDs
        tasks = []
        project_ids = set()
        for task_id in task_ids:
            task = self.task_repository.get_or_404(self.db, task_id)
            tasks.append(task)
            project_ids.add(task.project_id)
        
        # Validate team assignment if provided
        if team_id is not None:
            team = self.team_repository.get_or_404(self.db, team_id)
            # Check if team belongs to all the projects of the tasks
            for project_id in project_ids:
                if team.project_id != project_id:
                    raise BadRequestException(
                        f"Team {team_id} does not belong to all projects of the selected tasks"
                    )
        
        return self.task_repository.bulk_assign_to_team(self.db, ids=task_ids, team_id=team_id)
    
    def count_tasks_for_project(self, project_id: str) -> int:
        """Count the number of tasks for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The number of tasks for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        return self.task_repository.count_by_project(self.db, project_id=project_id)
    
    def count_tasks_for_team(self, team_id: int) -> int:
        """Count the number of tasks assigned to a team.
        
        Args:
            team_id: The ID of the team.
            
        Returns:
            The number of tasks assigned to the team.
            
        Raises:
            NotFoundException: If the team is not found.
        """
        # Check if team exists
        team = self.team_repository.get_or_404(self.db, team_id)
        
        return self.task_repository.count_by_team(self.db, team_id=team_id)
    
    def get_task_status_counts(self, project_id: str) -> Dict[TaskStatus, int]:
        """Get the count of tasks by status for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            A dictionary mapping status to count.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        return self.task_repository.get_status_counts(self.db, project_id=project_id)