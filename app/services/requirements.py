"""Requirement service."""

from typing import List

from app.repositories.requirements import RequirementRepository
from app.repositories.projects import ProjectRepository
from app.domain.models.requirements import Requirement
from app.api.schemas.requirements import RequirementCreate, RequirementUpdate
from app.core.exceptions import NotFoundException


class RequirementService:
    """Requirement service class."""
    
    def __init__(self, requirement_repository: RequirementRepository, project_repository: ProjectRepository):
        self.requirement_repository = requirement_repository
        self.project_repository = project_repository
    
    def create_requirement(self, project_id: str, requirement_data: RequirementCreate) -> Requirement:
        """Create a new requirement for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        
        return self.requirement_repository.create_for_project(project_id, requirement_data)
    
    def get_requirement(self, project_id: str, requirement_id: int) -> Requirement:
        """Get requirement by project ID and requirement ID."""
        requirement = self.requirement_repository.get_by_project_and_id(project_id, requirement_id)
        if not requirement:
            raise NotFoundException(f"Requirement with id {requirement_id} not found in project {project_id}")
        return requirement
    
    def list_requirements(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Requirement]:
        """List requirements for a project."""
        # Verify project exists
        project = self.project_repository.get_by_id(project_id)
        if not project:
            raise NotFoundException(f"Project with id {project_id} not found")
        
        return self.requirement_repository.get_by_project_id(project_id, skip=skip, limit=limit)
    
    def update_requirement(self, project_id: str, requirement_id: int, requirement_data: RequirementUpdate) -> Requirement:
        """Update requirement."""
        requirement = self.get_requirement(project_id, requirement_id)
        return self.requirement_repository.update(self.requirement_repository.db, db_obj=requirement, obj_in=requirement_data)
    
    def delete_requirement(self, project_id: str, requirement_id: int) -> None:
        """Delete requirement."""
        if not self.requirement_repository.delete_by_project_and_id(project_id, requirement_id):
            raise NotFoundException(f"Requirement with id {requirement_id} not found in project {project_id}")