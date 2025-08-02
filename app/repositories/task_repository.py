"""Task repository implementation.

This module provides a repository for Task entities.
It extends the base repository and adds task-specific query methods.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc

from app.repositories.base import CRUDRepository
from app.domain.models.tasks import Task, TaskStatus
from app.api.schemas.tasks import TaskCreate, TaskUpdate
from app.core.exceptions import NotFoundException, DatabaseException

class TaskRepository(CRUDRepository[Task, TaskCreate, TaskUpdate]):
    """Task repository class.
    
    This class provides CRUD operations and task-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the Task model."""
        super().__init__(Task)
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get tasks for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of tasks for the project.
        """
        return self.get_multi_by_field(db, "project_id", project_id, skip=skip, limit=limit)
    
    def get_by_team(self, db: Session, *, team_id: int, skip: int = 0, limit: int = 100) -> List[Task]:
        """Get tasks assigned to a team.
        
        Args:
            db: The database session.
            team_id: The ID of the team.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of tasks assigned to the team.
        """
        return self.get_multi_by_field(db, "assigned_to_team_id", team_id, skip=skip, limit=limit)
    
    def get_by_status(
        self, db: Session, *, project_id: str, status: TaskStatus, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by status for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            status: The task status.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of tasks with the specified status.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                self.model.status == status
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting tasks by status: {str(e)}", original_exception=e)
    
    def get_by_team_and_status(
        self, db: Session, *, team_id: int, status: TaskStatus, skip: int = 0, limit: int = 100
    ) -> List[Task]:
        """Get tasks by status for a team.
        
        Args:
            db: The database session.
            team_id: The ID of the team.
            status: The task status.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of tasks with the specified status assigned to the team.
        """
        try:
            return db.query(self.model).filter(
                self.model.assigned_to_team_id == team_id,
                self.model.status == status
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting tasks by team and status: {str(e)}", original_exception=e)
    
    def update_status(self, db: Session, *, id: int, status: TaskStatus) -> Task:
        """Update the status of a task.
        
        Args:
            db: The database session.
            id: The ID of the task.
            status: The new status.
            
        Returns:
            The updated task.
        """
        return self.update_by_id(db, id=id, obj_in={"status": status})
    
    def assign_to_team(self, db: Session, *, id: int, team_id: Optional[int]) -> Task:
        """Assign a task to a team.
        
        Args:
            db: The database session.
            id: The ID of the task.
            team_id: The ID of the team, or None to unassign.
            
        Returns:
            The updated task.
        """
        return self.update_by_id(db, id=id, obj_in={"assigned_to_team_id": team_id})
    
    def bulk_update_status(
        self, db: Session, *, ids: List[int], status: TaskStatus
    ) -> List[Task]:
        """Update the status of multiple tasks.
        
        Args:
            db: The database session.
            ids: The IDs of the tasks.
            status: The new status.
            
        Returns:
            The updated tasks.
        """
        return self.bulk_update(db, ids=ids, obj_in={"status": status})
    
    def bulk_assign_to_team(
        self, db: Session, *, ids: List[int], team_id: Optional[int]
    ) -> List[Task]:
        """Assign multiple tasks to a team.
        
        Args:
            db: The database session.
            ids: The IDs of the tasks.
            team_id: The ID of the team, or None to unassign.
            
        Returns:
            The updated tasks.
        """
        return self.bulk_update(db, ids=ids, obj_in={"assigned_to_team_id": team_id})
    
    def count_by_project(self, db: Session, *, project_id: str) -> int:
        """Count the number of tasks for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The number of tasks for the project.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting tasks: {str(e)}", original_exception=e)
    
    def count_by_team(self, db: Session, *, team_id: int) -> int:
        """Count the number of tasks assigned to a team.
        
        Args:
            db: The database session.
            team_id: The ID of the team.
            
        Returns:
            The number of tasks assigned to the team.
        """
        try:
            return db.query(self.model).filter(
                self.model.assigned_to_team_id == team_id
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting tasks by team: {str(e)}", original_exception=e)
    
    def count_by_status(self, db: Session, *, project_id: str, status: TaskStatus) -> int:
        """Count the number of tasks with a specific status for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            status: The task status.
            
        Returns:
            The number of tasks with the specified status.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                self.model.status == status
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting tasks by status: {str(e)}", original_exception=e)
    
    def get_status_counts(self, db: Session, *, project_id: str) -> Dict[TaskStatus, int]:
        """Get the count of tasks by status for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            A dictionary mapping status to count.
        """
        try:
            counts = {}
            for status in TaskStatus:
                counts[status] = self.count_by_status(db, project_id=project_id, status=status)
            return counts
        except Exception as e:
            raise DatabaseException(f"Error getting status counts: {str(e)}", original_exception=e)

# Create a singleton instance
task_repository = TaskRepository()