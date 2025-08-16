"""Note repository implementation.

This module provides a repository for Note entities.
It extends the base repository and adds Note-specific query methods.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.repositories.base import CRUDRepository
from app.domain.models.notes import Note
from app.api.schemas.notes import NoteCreate, NoteUpdate
from app.core.exceptions import NotFoundException, DatabaseException

class NoteRepository(CRUDRepository[Note, NoteCreate, NoteUpdate]):
    """Note repository class.
    
    This class provides CRUD operations and Note-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the Note model."""
        super().__init__(Note)
    
    def get_by_project(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[Note]:
        """Get notes for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of notes for the project.
        """
        return self.get_multi_by_field(db, "project_id", project_id, skip=skip, limit=limit)
    
    def get_by_title(self, db: Session, *, project_id: str, title: str) -> Optional[Note]:
        """Get a note by title for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            title: The title of the note.
            
        Returns:
            The note if found, None otherwise.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                self.model.title == title
            ).first()
        except Exception as e:
            raise DatabaseException(f"Error getting note by title: {str(e)}", original_exception=e)
    
    def search_notes(
        self, db: Session, *, project_id: str, query: str, skip: int = 0, limit: int = 100
    ) -> List[Note]:
        """Search notes by title, description, or content for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            query: The search query.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of notes matching the search query.
        """
        try:
            search_query = f"%{query}%"
            return db.query(self.model).filter(
                self.model.project_id == project_id,
                (self.model.title.ilike(search_query) | 
                 self.model.description.ilike(search_query) | 
                 self.model.content.ilike(search_query))
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error searching notes: {str(e)}", original_exception=e)
    
    def get_recent_notes(
        self, db: Session, *, project_id: str, limit: int = 5
    ) -> List[Note]:
        """Get recent notes for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            limit: The maximum number of records to return.
            
        Returns:
            A list of recent notes for the project.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id
            ).order_by(desc(self.model.created_at)).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting recent notes: {str(e)}", original_exception=e)
    
    def count_by_project(self, db: Session, *, project_id: str) -> int:
        """Count the number of notes for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The number of notes for the project.
        """
        try:
            return db.query(self.model).filter(
                self.model.project_id == project_id
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting notes: {str(e)}", original_exception=e)

# Create a singleton instance
note_repository = NoteRepository()