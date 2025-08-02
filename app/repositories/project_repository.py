"""Project repository implementation.

This module provides a repository for Project entities.
It extends the base repository and adds project-specific query methods.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_

from app.repositories.base import CRUDRepository
from app.domain.models.projects import Project, ProjectState
from app.api.schemas.projects import ProjectCreate, ProjectUpdate

class ProjectRepository(CRUDRepository[Project, ProjectCreate, ProjectUpdate]):
    """Project repository class.
    
    This class provides CRUD operations and project-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the Project model."""
        super().__init__(Project)
    
    def get_by_code(self, db: Session, code: str) -> Optional[Project]:
        """Get a project by code.
        
        Args:
            db: The database session.
            code: The project code.
            
        Returns:
            The project if found, None otherwise.
        """
        return self.get_by_field(db, "code", code)
    
    def get_by_state(self, db: Session, state: ProjectState, *, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get projects by state.
        
        Args:
            db: The database session.
            state: The project state.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of projects with the specified state.
        """
        return self.get_multi_by_field(db, "state", state, skip=skip, limit=limit)
    
    def get_active_projects(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get active projects.
        
        Args:
            db: The database session.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of active projects.
        """
        return self.get_by_state(db, ProjectState.active, skip=skip, limit=limit)
    
    def get_archived_projects(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get archived projects.
        
        Args:
            db: The database session.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of archived projects.
        """
        return self.get_by_state(db, ProjectState.archived, skip=skip, limit=limit)
    
    def search_projects(
        self, db: Session, *, query: str, skip: int = 0, limit: int = 100, include_archived: bool = False
    ) -> List[Project]:
        """Search projects by name, description, or code.
        
        Args:
            db: The database session.
            query: The search query.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            include_archived: Whether to include archived projects.
            
        Returns:
            A list of projects matching the search query.
        """
        search_query = f"%{query}%"
        filters = [
            Project.name.ilike(search_query),
            Project.description.ilike(search_query),
            Project.code.ilike(search_query)
        ]
        
        if not include_archived:
            state_filter = Project.state == ProjectState.active
        else:
            state_filter = Project.state != ProjectState.deleted
        
        return db.query(self.model).filter(
            and_(
                or_(*filters),
                state_filter
            )
        ).offset(skip).limit(limit).all()
    
    def archive_project(self, db: Session, *, id: str) -> Project:
        """Archive a project.
        
        Args:
            db: The database session.
            id: The ID of the project to archive.
            
        Returns:
            The archived project.
        """
        return self.update_by_id(db, id=id, obj_in={"state": ProjectState.archived})
    
    def restore_project(self, db: Session, *, id: str) -> Project:
        """Restore an archived project.
        
        Args:
            db: The database session.
            id: The ID of the project to restore.
            
        Returns:
            The restored project.
        """
        return self.update_by_id(db, id=id, obj_in={"state": ProjectState.active})
    
    def soft_delete_project(self, db: Session, *, id: str) -> Project:
        """Soft delete a project.
        
        Args:
            db: The database session.
            id: The ID of the project to delete.
            
        Returns:
            The deleted project.
        """
        return self.update_by_id(db, id=id, obj_in={"state": ProjectState.deleted})
    
    def get_with_relationships(self, db: Session, id: str) -> Optional[Project]:
        """Get a project with all relationships loaded.
        
        Args:
            db: The database session.
            id: The ID of the project to get.
            
        Returns:
            The project with relationships if found, None otherwise.
        """
        return db.query(self.model).filter(self.model.id == id).options(
            joinedload(Project.solution_outlines),
            joinedload(Project.adrs),
            joinedload(Project.teams),
            joinedload(Project.tasks)
        ).first()

# Create a singleton instance
project_repository = ProjectRepository()