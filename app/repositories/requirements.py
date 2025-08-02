"""Requirement repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.base import CRUDRepository
from app.domain.models.requirements import Requirement
from app.api.schemas.requirements import RequirementCreate, RequirementUpdate


class RequirementRepository(CRUDRepository[Requirement, RequirementCreate, RequirementUpdate]):
    """Requirement repository class."""
    
    def __init__(self, db: Session):
        super().__init__(Requirement)
        self.db = db
    
    def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Requirement]:
        """Get requirements by project ID."""
        return (
            self.db.query(self.model)
            .filter(self.model.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_project_and_id(self, project_id: str, requirement_id: int) -> Optional[Requirement]:
        """Get requirement by project ID and requirement ID."""
        return (
            self.db.query(self.model)
            .filter(
                self.model.project_id == project_id,
                self.model.id == requirement_id
            )
            .first()
        )
    
    def create_for_project(self, project_id: str, requirement_data: RequirementCreate) -> Requirement:
        """Create a new requirement for a project."""
        db_requirement = self.model(
            project_id=project_id,
            **requirement_data.model_dump()
        )
        self.db.add(db_requirement)
        self.db.commit()
        self.db.refresh(db_requirement)
        return db_requirement
    
    def delete_by_project_and_id(self, project_id: str, requirement_id: int) -> bool:
        """Delete requirement by project ID and requirement ID."""
        requirement = self.get_by_project_and_id(project_id, requirement_id)
        if requirement:
            self.db.delete(requirement)
            self.db.commit()
            return True
        return False