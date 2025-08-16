"""Notes API endpoints.

This module provides API endpoints for managing Notes.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import (
    get_pagination_params_dependency, 
    get_search_params, 
    get_filter_params
)
from app.services.notes import NoteService, note_service
from app.api.schemas.notes import NoteCreate, NoteUpdate, NoteUpsert, NoteResponse
from app.api.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams
from app.utils.filtering import parse_filter_params
from app.utils.response_utils import paginated_response

router = APIRouter(tags=["Notes"])

def get_note_service(db: Session = Depends(get_db)) -> NoteService:
    """Dependency to get note service."""
    return NoteService(db)

@router.post(
    "/projects/{project_id}/notes",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update a note (upsert)",
    description="Create a new note or update an existing one. If note_id is provided in the request body, the note will be updated; otherwise, a new note will be created."
)
def upsert_note(
    project_id: str = Path(..., description="The ID of the project"),
    note_data: NoteUpsert = ...,
    service: NoteService = Depends(get_note_service)
):
    """Create or update a note (upsert operation).
    
    Args:
        project_id: The ID of the project.
        note_data: The note data containing title, description, content, tags, and optional note_id.
        service: The note service.
        
    Returns:
        The created or updated note.
        
    Raises:
        NotFoundException: If the project or note (for update) is not found.
        ConflictException: If a note with the same title already exists for the project.
    """
    try:
        return service.upsert_note(project_id, note_data)
    except (NotFoundException, ConflictException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/notes/{note_id}",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a note by ID",
    description="Get a note by its ID."
)
def get_note(
    note_id: int = Path(..., description="The ID of the note"),
    service: NoteService = Depends(get_note_service)
):
    """Get a note by ID.
    
    Args:
        note_id: The ID of the note.
        service: The note service.
        
    Returns:
        The note.
        
    Raises:
        NotFoundException: If the note is not found.
    """
    try:
        return service.get_note(note_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/notes",
    response_model=PaginatedResponse[NoteResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all notes for a project",
    description="Get all notes for a project with pagination, filtering, and search support."
)
def get_notes_for_project(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    search: Optional[str] = Depends(get_search_params),
    filter_params: Dict[str, Any] = Depends(get_filter_params),
    service: NoteService = Depends(get_note_service)
):
    """Get all notes for a project with pagination, filtering, and search.
    
    Args:
        request: The FastAPI request object.
        project_id: The ID of the project.
        pagination: Pagination parameters.
        search: Search term.
        filter_params: Filter parameters.
        service: The note service.
        
    Returns:
        Paginated list of notes for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        # Parse filter conditions
        filters = parse_filter_params(filter_params) if filter_params else None
        
        # Get paginated notes
        result = service.get_notes_for_project(project_id, pagination, filters, search)
        
        # Return paginated response
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="Notes retrieved successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete(
    "/notes/{note_id}",
    response_model=NoteResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a note",
    description="Delete a note."
)
def delete_note(
    note_id: int = Path(..., description="The ID of the note"),
    service: NoteService = Depends(get_note_service)
):
    """Delete a note.
    
    Args:
        note_id: The ID of the note.
        service: The note service.
        
    Returns:
        The deleted note.
        
    Raises:
        NotFoundException: If the note is not found.
    """
    try:
        return service.delete_note(note_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/notes/search",
    response_model=PaginatedResponse[NoteResponse],
    status_code=status.HTTP_200_OK,
    summary="Search notes",
    description="Search notes by title, description, or content for a project with pagination support."
)
def search_notes(
    project_id: str = Path(..., description="The ID of the project"),
    query: str = Query(..., description="The search query"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    service: NoteService = Depends(get_note_service)
):
    """Search notes with pagination support.
    
    Args:
        project_id: The ID of the project.
        query: The search query.
        pagination: Pagination parameters.
        service: The note service.
        
    Returns:
        Paginated list of notes matching the search query.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        result = service.search_notes(project_id, query, pagination)
        
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="Notes search completed successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/notes/recent",
    response_model=List[NoteResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent notes",
    description="Get recent notes for a project."
)
def get_recent_notes(
    project_id: str = Path(..., description="The ID of the project"),
    limit: int = Query(5, description="The maximum number of records to return"),
    service: NoteService = Depends(get_note_service)
):
    """Get recent notes.
    
    Args:
        project_id: The ID of the project.
        limit: The maximum number of records to return.
        service: The note service.
        
    Returns:
        A list of recent notes for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.get_recent_notes(project_id, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/notes/count",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Count notes for a project",
    description="Count the number of notes for a project."
)
def count_notes_for_project(
    project_id: str = Path(..., description="The ID of the project"),
    service: NoteService = Depends(get_note_service)
):
    """Count notes for a project.
    
    Args:
        project_id: The ID of the project.
        service: The note service.
        
    Returns:
        The number of notes for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.count_notes_for_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)