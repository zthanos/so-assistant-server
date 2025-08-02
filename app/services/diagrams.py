"""Diagram service."""

from typing import List

from app.repositories.diagrams import DiagramRepository
from app.repositories.projects import ProjectRepository
from app.domain.models.diagrams import Diagram
from app.api.schemas.diagrams import DiagramCreate, DiagramUpdate
from app.core.exceptions import NotFoundException


class DiagramService:
    """Diagram service class."""
    
    def __init__(self, diagram_repository: DiagramRepository, project_repository: ProjectRepository):
        self.diagram_repository = diagram_repository
        self.project_repository = project_repository
    
    def create_diagram(self, project_id: str, diagram_data: DiagramCreate) -> Diagram:
        """Create a new diagram for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        
        return self.diagram_repository.create_for_project(project_id, diagram_data)
    
    def get_diagram(self, project_id: str, diagram_id: int) -> Diagram:
        """Get diagram by project ID and diagram ID."""
        diagram = self.diagram_repository.get_by_project_and_id(project_id, diagram_id)
        if not diagram:
            raise NotFoundException(f"Diagram with id {diagram_id} not found in project {project_id}")
        return diagram
    
    def list_diagrams(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Diagram]:
        """List diagrams for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        
        return self.diagram_repository.get_by_project_id(project_id, skip=skip, limit=limit)
    
    def update_diagram(self, project_id: str, diagram_id: int, diagram_data: DiagramUpdate) -> Diagram:
        """Update diagram."""
        diagram = self.get_diagram(project_id, diagram_id)
        return self.diagram_repository.update(self.diagram_repository.db, db_obj=diagram, obj_in=diagram_data)
    
    def delete_diagram(self, project_id: str, diagram_id: int) -> None:
        """Delete diagram."""
        if not self.diagram_repository.delete_by_project_and_id(project_id, diagram_id):
            raise NotFoundException(f"Diagram with id {diagram_id} not found in project {project_id}")