"""Note service implementation.

This module provides a service for managing Notes.
It follows the service pattern and provides a clean interface for Note operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.repositories.note_repository import note_repository
from app.repositories.project_repository import project_repository
from app.domain.models.notes import Note
from app.api.schemas.notes import NoteCreate, NoteUpdate, NoteUpsert, NoteResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams, PaginationResult, Paginator
from app.utils.filtering import FilterCondition, QueryFilter

class NoteService:
    """Note service class.
    
    This class provides business logic for managing Notes.
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.note_repository = note_repository
        self.project_repository = project_repository
    
    def create_note(self, project_id: str, note_data: NoteCreate) -> NoteResponse:
        """Create a new note.
        
        Args:
            project_id: The ID of the project.
            note_data: The note creation data.
            
        Returns:
            The created note.
            
        Raises:
            NotFoundException: If the project is not found.
            ConflictException: If a note with the same title already exists for the project.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Check if note with same title exists
        existing_note = self.note_repository.get_by_title(self.db, project_id=project_id, title=note_data.title)
        if existing_note:
            raise ConflictException(
                f"Note with title '{note_data.title}' already exists for project {project_id}",
                resource_type="Note",
                resource_id=existing_note.id
            )
        
        # Create note
        note = self.note_repository.create(self.db, obj_in=note_data)
        return NoteResponse.from_orm(note)
    
    def get_note(self, note_id: int) -> NoteResponse:
        """Get a note by ID.
        
        Args:
            note_id: The ID of the note.
            
        Returns:
            The note.
            
        Raises:
            NotFoundException: If the note is not found.
        """
        note = self.note_repository.get_or_404(self.db, note_id)
        return NoteResponse.from_orm(note)
    
    def get_notes_for_project(
        self, 
        project_id: str, 
        pagination: PaginationParams,
        filters: Optional[List[FilterCondition]] = None,
        search: Optional[str] = None
    ) -> PaginationResult[NoteResponse]:
        """Get all notes for a project with pagination and filtering.
        
        Args:
            project_id: The ID of the project.
            pagination: Pagination parameters.
            filters: List of filter conditions.
            search: Search term.
            
        Returns:
            Paginated result of notes for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(Note).filter(Note.project_id == project_id)
        
        # Apply filters
        if filters:
            allowed_fields = ["title", "description", "content", "created_at", "updated_at"]
            query = QueryFilter.apply_filters(query, filters, Note, allowed_fields)
        
        # Apply search
        if search:
            search_fields = ["title", "description", "content"]
            query = QueryFilter.apply_search(query, search, search_fields, Note)
        
        # Apply pagination
        allowed_sort_fields = ["title", "created_at", "updated_at"]
        result = Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
        
        # Convert SQLAlchemy models to Pydantic models
        note_responses = [NoteResponse.from_orm(note) for note in result.items]
        
        return PaginationResult(
            items=note_responses,
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            pages=result.pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )
    
    def update_note(self, note_id: int, update_data: NoteUpdate) -> NoteResponse:
        """Update a note.
        
        Args:
            note_id: The ID of the note.
            update_data: The note update data.
            
        Returns:
            The updated note.
            
        Raises:
            NotFoundException: If the note is not found.
            ConflictException: If a note with the same title already exists for the project.
            BadRequestException: If no update fields are provided.
        """
        # Check if note exists
        note = self.note_repository.get_or_404(self.db, note_id)
        
        # Check if any update fields are provided
        update_dict = update_data.model_dump(exclude_unset=True)
        if not update_dict:
            raise BadRequestException("No update fields provided")
        
        # Check if title is being updated and if it conflicts with existing note
        if update_data.title is not None and update_data.title != note.title:
            existing_note = self.note_repository.get_by_title(self.db, project_id=note.project_id, title=update_data.title)
            if existing_note and existing_note.id != note_id:
                raise ConflictException(
                    f"Note with title '{update_data.title}' already exists for project {note.project_id}",
                    resource_type="Note",
                    resource_id=existing_note.id
                )
        
        updated_note = self.note_repository.update(self.db, db_obj=note, obj_in=update_data)
        return NoteResponse.from_orm(updated_note)
    
    def delete_note(self, note_id: int) -> NoteResponse:
        """Delete a note.
        
        Args:
            note_id: The ID of the note.
            
        Returns:
            The deleted note.
            
        Raises:
            NotFoundException: If the note is not found.
        """
        # Check if note exists
        note = self.note_repository.get_or_404(self.db, note_id)
        
        deleted_note = self.note_repository.delete(self.db, id=note_id)
        return NoteResponse.from_orm(deleted_note)
    
    def search_notes(
        self, 
        project_id: str, 
        search_query: str, 
        pagination: PaginationParams
    ) -> PaginationResult[NoteResponse]:
        """Search notes by title, description, or content for a project.
        
        Args:
            project_id: The ID of the project.
            search_query: The search query.
            pagination: Pagination parameters.
            
        Returns:
            Paginated result of notes matching the search query.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(Note).filter(Note.project_id == project_id)
        
        # Apply search
        search_fields = ["title", "description", "content"]
        query = QueryFilter.apply_search(query, search_query, search_fields, Note)
        
        # Apply pagination
        allowed_sort_fields = ["title", "created_at", "updated_at"]
        result = Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
        
        # Convert SQLAlchemy models to Pydantic models
        note_responses = [NoteResponse.from_orm(note) for note in result.items]
        
        return PaginationResult(
            items=note_responses,
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            pages=result.pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )
    
    def get_recent_notes(self, project_id: str, limit: int = 5) -> List[NoteResponse]:
        """Get recent notes for a project.
        
        Args:
            project_id: The ID of the project.
            limit: The maximum number of records to return.
            
        Returns:
            A list of recent notes for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        notes = self.note_repository.get_recent_notes(self.db, project_id=project_id, limit=limit)
        return [NoteResponse.from_orm(note) for note in notes]
    
    def count_notes_for_project(self, project_id: str) -> int:
        """Count the number of notes for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The number of notes for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        return self.note_repository.count_by_project(self.db, project_id=project_id)
    
    def upsert_note(self, project_id: str, upsert_data: NoteUpsert) -> NoteResponse:
        """Create or update a note (upsert operation).
        
        Args:
            project_id: The ID of the project.
            upsert_data: The upsert data containing title, description, content, tags, and optional note_id.
            
        Returns:
            The created or updated note.
            
        Raises:
            NotFoundException: If the project or note (for update) is not found.
            ConflictException: If a note with the same title already exists for the project.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        if upsert_data.note_id is not None:
            # Update existing note
            note = self.note_repository.get_or_404(self.db, upsert_data.note_id)
            
            # Verify the note belongs to the specified project
            if note.project_id != project_id:
                raise NotFoundException(
                    f"Note {upsert_data.note_id} not found in project {project_id}",
                    resource_type="Note"
                )
            
            # Check if title conflicts with another note in the same project
            existing_note = self.note_repository.get_by_title(
                self.db, project_id=project_id, title=upsert_data.title
            )
            if existing_note and existing_note.id != upsert_data.note_id:
                raise ConflictException(
                    f"Note with title '{upsert_data.title}' already exists for project {project_id}",
                    resource_type="Note",
                    resource_id=existing_note.id
                )
            
            # Update the note
            update_data = NoteUpdate(
                title=upsert_data.title,
                description=upsert_data.description,
                content=upsert_data.content,
                tags=upsert_data.tags
            )
            updated_note = self.note_repository.update(self.db, db_obj=note, obj_in=update_data)
            return NoteResponse.from_orm(updated_note)
        
        else:
            # Create new note
            # Check if note with same title exists
            existing_note = self.note_repository.get_by_title(
                self.db, project_id=project_id, title=upsert_data.title
            )
            if existing_note:
                raise ConflictException(
                    f"Note with title '{upsert_data.title}' already exists for project {project_id}",
                    resource_type="Note",
                    resource_id=existing_note.id
                )
            
            # Create note
            note_data = NoteCreate(
                project_id=project_id,
                title=upsert_data.title,
                description=upsert_data.description,
                content=upsert_data.content,
                tags=upsert_data.tags
            )
            
            note = self.note_repository.create(self.db, obj_in=note_data)
            return NoteResponse.from_orm(note)

# Create a singleton instance
note_service = NoteService()