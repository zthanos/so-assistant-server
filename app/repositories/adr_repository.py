"""Architecture Decision Record (ADR) repository implementation.

This module provides a repository for ADR entities.
It extends the base repository and adds ADR-specific query methods.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.repositories.base import CRUDRepository
from app.domain.models.adrs import ADR
from app.api.schemas.adrs import ADRCreate, ADRUpdate
from app.core.exceptions import NotFoundException, DatabaseException

class ADRRepository(CRUDRepository[ADR, ADRCreate, ADRUpdate]):
    """ADR repository class.
    
    This class provides CRUD operations and ADR-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the ADR model."""
        super().__init__(ADR)
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[ADR]:
        """Get ADRs for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of ADRs for the project.
        """
        return self.get_multi_by_field(db, "project_id", project_id, skip=skip, limit=limit)
    
    def get_by_title(self, db: Session, *, project_id: str, title: str) -> Optional[ADR]:
        """Get an ADR by title for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            title: The title of the ADR.
            
        Returns:
            The ADR if found, None otherwise.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                self.model.title == title
            ).first()
        except Exception as e:
            raise DatabaseException(f"Error getting ADR by title: {str(e)}", original_exception=e)
    
    def search_adrs(
        self, db: Session, *, project_id: str, query: str, skip: int = 0, limit: int = 100
    ) -> List[ADR]:
        """Search ADRs by title or content for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            query: The search query.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of ADRs matching the search query.
        """
        try:
            search_query = f"%{query}%"
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                (self.model.title.ilike(search_query) | self.model.content.ilike(search_query))
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error searching ADRs: {str(e)}", original_exception=e)
    
    def get_recent_adrs(
        self, db: Session, *, project_id: str, limit: int = 5
    ) -> List[ADR]:
        """Get recent ADRs for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            limit: The maximum number of records to return.
            
        Returns:
            A list of recent ADRs for the project.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id
            ).order_by(desc(self.model.created_at)).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting recent ADRs: {str(e)}", original_exception=e)
    
    def count_by_project(self, db: Session, *, project_id: str) -> int:
        """Count the number of ADRs for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The number of ADRs for the project.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting ADRs: {str(e)}", original_exception=e)

# Create a singleton instance
adr_repository = ADRRepository()