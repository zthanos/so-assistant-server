"""Diagram repository."""

from typing import List, Optional
from sqlalchemy.orm import Session

from app.repositories.base import CRUDRepository
from app.domain.models.diagrams import Diagram
from app.api.schemas.diagrams import DiagramCreate, DiagramUpdate


class DiagramRepository(CRUDRepository[Diagram, DiagramCreate, DiagramUpdate]):
    """Diagram repository class."""
    
    def __init__(self, db: Session):
        super().__init__(Diagram)
        self.db = db
    
    def get_by_project_id(self, project_id: str, skip: int = 0, limit: int = 100) -> List[Diagram]:
        """Get diagrams by project ID."""
        return (
            self.db.query(self.model)
            .filter(self.model.project_id == project_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_project_and_id(self, project_id: str, diagram_id: int) -> Optional[Diagram]:
        """Get diagram by project ID and diagram ID."""
        return (
            self.db.query(self.model)
            .filter(
                self.model.project_id == project_id,
                self.model.id == diagram_id
            )
            .first()
        )
    
    def create_for_project(self, project_id: str, diagram_data: DiagramCreate) -> Diagram:
        """Create a new diagram for a project."""
        db_diagram = self.model(
            project_id=project_id,
            **diagram_data.model_dump()
        )
        self.db.add(db_diagram)
        self.db.commit()
        self.db.refresh(db_diagram)
        return db_diagram
    
    def delete_by_project_and_id(self, project_id: str, diagram_id: int) -> bool:
        """Delete diagram by project ID and diagram ID."""
        diagram = self.get_by_project_and_id(project_id, diagram_id)
        if diagram:
            self.db.delete(diagram)
            self.db.commit()
            return True
        return False