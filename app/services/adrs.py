"""Architecture Decision Record (ADR) service implementation.

This module provides a service for managing Architecture Decision Records (ADRs).
It follows the service pattern and provides a clean interface for ADR operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.repositories.adr_repository import adr_repository
from app.repositories.project_repository import project_repository
from app.domain.models.adrs import ADR
from app.api.schemas.adrs import ADRCreate, ADRUpdate, ADRResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams, PaginationResult, Paginator
from app.utils.filtering import FilterCondition, QueryFilter

class ADRService:
    """ADR service class.
    
    This class provides business logic for managing Architecture Decision Records (ADRs).
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.adr_repository = adr_repository
        self.project_repository = project_repository
    
    def create_adr(self, project_id: str, title: str, content: str) -> ADR:
        """Create a new ADR.
        
        Args:
            project_id: The ID of the project.
            title: The title of the ADR.
            content: The content of the ADR.
            
        Returns:
            The created ADR.
            
        Raises:
            NotFoundException: If the project is not found.
            ConflictException: If an ADR with the same title already exists for the project.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Check if ADR with same title exists
        existing_adr = self.adr_repository.get_by_title(self.db, project_id=project_id, title=title)
        if existing_adr:
            raise ConflictException(
                f"ADR with title '{title}' already exists for project {project_id}",
                resource_type="ADR",
                conflict_field="title"
            )
        
        # Create ADR
        adr_data = ADRCreate(
            project_id=project_id,
            title=title,
            content=content
        )
        
        return self.adr_repository.create(self.db, obj_in=adr_data)
    
    def get_adr(self, adr_id: int) -> ADR:
        """Get an ADR by ID.
        
        Args:
            adr_id: The ID of the ADR.
            
        Returns:
            The ADR.
            
        Raises:
            NotFoundException: If the ADR is not found.
        """
        return self.adr_repository.get_or_404(self.db, adr_id)
    
    def get_adrs_for_project(
        self, 
        project_id: str, 
        pagination: PaginationParams,
        filters: Optional[List[FilterCondition]] = None,
        search: Optional[str] = None
    ) -> PaginationResult[ADR]:
        """Get all ADRs for a project with pagination and filtering.
        
        Args:
            project_id: The ID of the project.
            pagination: Pagination parameters.
            filters: List of filter conditions.
            search: Search term.
            
        Returns:
            Paginated result of ADRs for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(ADR).filter(ADR.project_id == project_id)
        
        # Apply filters
        if filters:
            allowed_fields = ["title", "content", "created_at", "updated_at"]
            query = QueryFilter.apply_filters(query, filters, ADR, allowed_fields)
        
        # Apply search
        if search:
            search_fields = ["title", "content"]
            query = QueryFilter.apply_search(query, search, search_fields, ADR)
        
        # Apply pagination
        allowed_sort_fields = ["title", "created_at", "updated_at"]
        return Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
    
    def update_adr(self, adr_id: int, title: Optional[str] = None, content: Optional[str] = None) -> ADR:
        """Update an ADR.
        
        Args:
            adr_id: The ID of the ADR.
            title: The new title of the ADR.
            content: The new content of the ADR.
            
        Returns:
            The updated ADR.
            
        Raises:
            NotFoundException: If the ADR is not found.
            ConflictException: If an ADR with the same title already exists for the project.
            BadRequestException: If no update fields are provided.
        """
        # Check if ADR exists
        adr = self.adr_repository.get_or_404(self.db, adr_id)
        
        # Check if update fields are provided
        if title is None and content is None:
            raise BadRequestException("No update fields provided")
        
        # Check if title is being updated and if it conflicts with existing ADR
        if title is not None and title != adr.title:
            existing_adr = self.adr_repository.get_by_title(self.db, project_id=adr.project_id, title=title)
            if existing_adr and existing_adr.id != adr_id:
                raise ConflictException(
                    f"ADR with title '{title}' already exists for project {adr.project_id}",
                    resource_type="ADR",
                    conflict_field="title"
                )
        
        # Create update data
        update_data = ADRUpdate(
            title=title if title is not None else adr.title,
            content=content if content is not None else adr.content
        )
        
        return self.adr_repository.update(self.db, db_obj=adr, obj_in=update_data)
    
    def delete_adr(self, adr_id: int) -> ADR:
        """Delete an ADR.
        
        Args:
            adr_id: The ID of the ADR.
            
        Returns:
            The deleted ADR.
            
        Raises:
            NotFoundException: If the ADR is not found.
        """
        # Check if ADR exists
        adr = self.adr_repository.get_or_404(self.db, adr_id)
        
        return self.adr_repository.delete(self.db, id=adr_id)
    
    def search_adrs(
        self, 
        project_id: str, 
        search_query: str, 
        pagination: PaginationParams
    ) -> PaginationResult[ADR]:
        """Search ADRs by title or content for a project.
        
        Args:
            project_id: The ID of the project.
            search_query: The search query.
            pagination: Pagination parameters.
            
        Returns:
            Paginated result of ADRs matching the search query.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(ADR).filter(ADR.project_id == project_id)
        
        # Apply search
        search_fields = ["title", "content"]
        query = QueryFilter.apply_search(query, search_query, search_fields, ADR)
        
        # Apply pagination
        allowed_sort_fields = ["title", "created_at", "updated_at"]
        return Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
    
    def get_recent_adrs(self, project_id: str, limit: int = 5) -> List[ADR]:
        """Get recent ADRs for a project.
        
        Args:
            project_id: The ID of the project.
            limit: The maximum number of records to return.
            
        Returns:
            A list of recent ADRs for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        return self.adr_repository.get_recent_adrs(self.db, project_id=project_id, limit=limit)
    
    def count_adrs_for_project(self, project_id: str) -> int:
        """Count the number of ADRs for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The number of ADRs for the project.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        return self.adr_repository.count_by_project(self.db, project_id=project_id)

# Create a singleton instance
adr_service = ADRService()