"""Project service."""

from typing import List, Optional

from app.repositories.projects import ProjectRepository
from app.domain.models import Project
from app.api.schemas.projects import ProjectCreate, ProjectUpdate
from app.core.exceptions import NotFoundException
from sqlalchemy.inspection import inspect


class ProjectService:
    """Project service class."""
    
    def __init__(self, repository: ProjectRepository):
        self.repository = repository
    
    def create_project(self, project_data: ProjectCreate) -> Project:
        """Create a new project."""
        return self.repository.create(self.repository.db, obj_in=project_data)
    
    def get_project(self, project_id: str) -> Project:
        """Get project by ID."""
        project = self.repository.get_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        return project
    
    def get_project_outline(self, project_id: str) -> Project:
        """Get project outline with all related entities."""
        project = self.repository.get_project_outline(project_id)
                
        debug_project(project)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        return project
    
    def list_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects."""
        return self.repository.list_projects(skip=skip, limit=limit)
    
    def update_project(self, project_id: str, project_data: ProjectUpdate) -> Project:
        """Update project."""
        project = self.get_project(project_id)
        return self.repository.update(self.repository.db, db_obj=project, obj_in=project_data)
    
    def delete_project(self, project_id: str) -> None:
        """Delete project."""
        if not self.repository.delete_by_id(project_id):
            raise NotFoundException(f"Project with id {project_id} not found")
        
def debug_project(project):
    mapper = inspect(project)
    print("Columns:")
    for column in mapper.attrs:
        try:
            print(f"  {column.key}: {getattr(project, column.key)}")
        except Exception as e:
            print(f"  {column.key}: <error: {e}>")        