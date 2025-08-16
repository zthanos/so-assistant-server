"""Project repository."""

import app.api.v1.endpoints
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload, aliased, contains_eager
from sqlalchemy import select, func

from app.repositories.base import CRUDRepository
from app.domain.models import Project
from app.domain.models.solution_outlines import  SolutionOutline
from app.domain.models.requirements import RequirementDocument
from app.api.schemas.projects import ProjectCreate, ProjectUpdate
from app.domain.models.requirements import RequirementDocument


class ProjectRepository(CRUDRepository[Project, ProjectCreate, ProjectUpdate]):
    """Project repository class."""
    
    def __init__(self, db: Session):
        super().__init__(Project)
        self.db = db
    
    def get_by_id(self, project_id: str) -> Optional[Project]:
        """Get project by ID."""
        return self.db.query(self.model).filter(self.model.id == project_id).first()
    
    # def get_project_outline(self, project_id: str) -> Optional[Project]:
    #     """Get project with all related entities for outline."""
    #     return (
    #         self.db.query(self.model)
    #         .options(
    #             joinedload(self.model.requirement_documents),
    #             joinedload(self.model.requirement_items),
    #             joinedload(self.model.solution_outlines),
    #             joinedload(self.model.systems),
    #             joinedload(self.model.adrs),
    #             joinedload(self.model.diagrams),
    #             joinedload(self.model.teams),
    #             joinedload(self.model.tasks)
    #         )
    #         .filter(self.model.id == project_id)
    #         .first()
    #     )
        


    def get_project_outline(self, project_id: str) -> Optional[Project]:
        # Subquery 1: latest SolutionOutline per project
        latest_solution_subq = (
            select(
                SolutionOutline.project_id,
                func.max(SolutionOutline.version).label("max_version")
            )
            .group_by(SolutionOutline.project_id)
            .subquery()
        )
        latest_solution_alias = aliased(SolutionOutline)

        # Subquery 2: latest RequirementDocument per project
        latest_req_doc_subq = (
            select(
                RequirementDocument.project_id,
                func.max(RequirementDocument.version).label("max_version")
            )
            .group_by(RequirementDocument.project_id)
            .subquery()
        )
        latest_req_doc_alias = aliased(RequirementDocument)

        # Main query
        return (
            self.db.query(Project)
            # JOIN στο subquery για solution outline
            .outerjoin(
                latest_solution_subq,
                latest_solution_subq.c.project_id == Project.id
            )
            .outerjoin(
                latest_solution_alias,
                (latest_solution_alias.project_id == Project.id) &
                (latest_solution_alias.version == latest_solution_subq.c.max_version)
            )
            # JOIN στο subquery για requirement document
            .outerjoin(
                latest_req_doc_subq,
                latest_req_doc_subq.c.project_id == Project.id
            )
            .outerjoin(
                latest_req_doc_alias,
                (latest_req_doc_alias.project_id == Project.id) &
                (latest_req_doc_alias.version == latest_req_doc_subq.c.max_version)
            )
            .options(
                contains_eager(Project.solution_outlines, alias=latest_solution_alias),
                contains_eager(Project.requirement_documents, alias=latest_req_doc_alias),
                joinedload(Project.systems),
                joinedload(Project.teams),
                joinedload(Project.tasks),
                joinedload(Project.diagrams),
                joinedload(Project.adrs),
            )
            .filter(Project.id == project_id)
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