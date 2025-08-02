"""Project repository."""

from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.repositories.base import CRUDRepository
from app.domain.models import Project
from app.api.schemas.projects import ProjectCreate, ProjectUpdate


class ProjectRepository(CRUDRepository[Project, ProjectCreate, ProjectUpdate]):
    """Project repository class."""
    
    def __init__(self, db: Session):
        super().__init__(Project)
        self.db = db
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self.db.query(self.model).filter(self.model.id == project_id).first()
    
    def get_project_outline(self, project_id: str) -> Optional[Project]:
        """Get project with all related entities for outline."""
        return (
            self.db.query(self.model)
            .options(
                joinedload(self.model.requirements),
                joinedload(self.model.diagrams),
                joinedload(self.model.teams),
                joinedload(self.model.tasks)
            )
            .filter(self.model.id == project_id)
            .first()
        )
    
    def list_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects with pagination."""
        return (
            self.db.query(self.model)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def delete_by_id(self, project_id: str) -> bool:
        """Delete project by ID."""
        project = self.get_by_id(project_id)
        if project:
            self.db.delete(project)
            self.db.commit()
            return True
        return False