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
from app.api.schemas.adrs import ADRCreate, ADRUpdate, ADRUpsert, ADRResponse
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
    
    # def create_adr(self, project_id: str, title: str, content: str) -> ADRResponse:
    #     """Create a new ADR.
        
    #     Args:
    #         project_id: The ID of the project.
    #         title: The title of the ADR.
    #         content: The content of the ADR.
            
    #     Returns:
    #         The created ADR.
            
    #     Raises:
    #         NotFoundException: If the project is not found.
    #         ConflictException: If an ADR with the same title already exists for the project.
    #     """
    #     # Check if project exists
    #     project = self.project_repository.get_or_404(self.db, project_id)
        
    #     # Check if ADR with same title exists
    #     existing_adr = self.adr_repository.get_by_title(self.db, project_id=project_id, title=title)
    #     if existing_adr:
    #         raise ConflictException(
    #             f"ADR with title '{title}' already exists for project {project_id}",
    #             resource_type="ADR",
    #             resource_id=existing_adr.id
    #         )
        
    #     # Create ADR
    #     adr_data = ADRCreate(
    #         project_id=project_id,
    #         title=title,
    #         content=content
    #     )
        
    #     adr = self.adr_repository.create(self.db, obj_in=adr_data)
    #     return ADRResponse.from_orm(adr)
    
    def get_adr(self, adr_id: int) -> ADRResponse:
        """Get an ADR by ID.
        
        Args:
            adr_id: The ID of the ADR.
            
        Returns:
            The ADR.
            
        Raises:
            NotFoundException: If the ADR is not found.
        """
        return  self.adr_repository.get_or_404(self.db, adr_id)

    def get_adrs_for_project(
        self, 
        project_id: str, 
        pagination: PaginationParams,
        filters: Optional[List[FilterCondition]] = None,
        search: Optional[str] = None
    ) -> PaginationResult[ADRResponse]:
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
        allowed_sort_fields = ["title", "status", "author", "created_at", "updated_at"]
        result = Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
        
        # Convert SQLAlchemy models to Pydantic models
        adr_responses = to_response(ADRResponse, result.items)
        
        return PaginationResult(
            items=adr_responses,
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            pages=result.pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )
    
    def update_adr(self, adr_id: int, title: Optional[str] = None, content: Optional[str] = None) -> ADRResponse:
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
                    resource_id=existing_adr.id
                )
        
        # Create update data
        update_data = ADRUpdate(
            title=title if title is not None else adr.title,
            content=content if content is not None else adr.content
        )
        
        updated_adr = self.adr_repository.update(self.db, db_obj=adr, obj_in=update_data)
        return to_response(ADRResponse, updated_adr.items)
    
    def delete_adr(self, adr_id: int) -> ADRResponse:
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
        
        deleted_adr = self.adr_repository.delete(self.db, id=adr_id)
        return to_response(ADRResponse, deleted_adr)
    
    def search_adrs(
        self, 
        project_id: str, 
        search_query: str, 
        pagination: PaginationParams
    ) -> PaginationResult[ADRResponse]:
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
        result = Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
        
        # Convert SQLAlchemy models to Pydantic models
        adr_responses = [
            ADRResponse.model_validate(row, from_attributes=True)
            for row in result.items
        ]
        
        return PaginationResult(
            items=adr_responses,
            total=result.total,
            page=result.page,
            per_page=result.per_page,
            pages=result.pages,
            has_next=result.has_next,
            has_prev=result.has_prev
        )
    
    def get_recent_adrs(self, project_id: str, limit: int = 5) -> List[ADRResponse]:
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
        
        adrs = self.adr_repository.get_recent_adrs(self.db, project_id=project_id, limit=limit)
        
        return to_response(ADRResponse, adrs.items)
    
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
    
    def upsert_adr(self, project_id: str, upsert_data: ADRUpsert) -> ADRResponse:
        """Create or update an ADR (upsert operation).
        
        Args:
            project_id: The ID of the project.
            upsert_data: The upsert data containing title, content, and optional adr_id.
            
        Returns:
            The created or updated ADR.
            
        Raises:
            NotFoundException: If the project or ADR (for update) is not found.
            ConflictException: If an ADR with the same title already exists for the project.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        if upsert_data.id is not None:
            # Update existing ADR
            adr = self.adr_repository.get_or_404(self.db, upsert_data.id)
            
            # Verify the ADR belongs to the specified project
            if adr.project_id != project_id:
                raise NotFoundException(
                    f"ADR {upsert_data.adr_id} not found in project {project_id}",
                    resource_type="ADR"
                )
            
            # Check if title conflicts with another ADR in the same project
            existing_adr = self.adr_repository.get_by_title(
                self.db, project_id=project_id, title=upsert_data.title
            )
            if existing_adr and existing_adr.id != upsert_data.id:
                raise ConflictException(
                    f"ADR with title '{upsert_data.title}' already exists for project {project_id}",
                    resource_type="ADR",
                    resource_id=existing_adr.id
                )
            
            # Update the ADR
            update_data = ADRUpdate(
                title=upsert_data.title,
                status=upsert_data.status,
                content=upsert_data.content,
                context=upsert_data.context,
                consequences=upsert_data.consequences,
                tags=upsert_data.tags,
                author=upsert_data.author,
                alternatives=upsert_data.alternatives,
                decision=upsert_data.decision, 
                id=upsert_data.id
            )
            updated_adr = self.adr_repository.update(self.db, db_obj=adr, obj_in=update_data)
            return updated_adr
        
        else:
            # Create new ADR
            # Check if ADR with same title exists
            existing_adr = self.adr_repository.get_by_title(
                self.db, project_id=project_id, title=upsert_data.title
            )
            if existing_adr:
                raise ConflictException(
                    f"ADR with title '{upsert_data.title}' already exists for project {project_id}",
                    resource_type="ADR",
                    resource_id=existing_adr.id
                )
            
            # Create ADR
            adr_data = ADRCreate(
                project_id=project_id,
                title=upsert_data.title,
                content=upsert_data.content
            )
            
            adr = self.adr_repository.create(self.db, obj_in=adr_data)
            return to_response(ADRResponse, adr.items)


# Create a singleton instance
adr_service = ADRService()


def to_response(model_cls, items):
    return [model_cls.model_validate(i, from_attributes=True) for i in items]