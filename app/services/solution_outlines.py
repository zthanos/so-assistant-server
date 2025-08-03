"""Solution Outline service implementation.

This module provides a service for managing solution outlines, including versioning logic.
It follows the service pattern and provides a clean interface for solution outline operations.
"""
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.repositories.solution_outline_repository import solution_outline_repository
from app.repositories.project_repository import project_repository
from app.domain.models.solution_outlines import SolutionOutline, SolutionOutlineStatus
from app.api.schemas.solution_outlines import (
    SolutionOutlineCreate, 
    SolutionOutlineUpdate, 
    SolutionOutlineResponse,
    SolutionOutlineVersionInfo
)
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams, PaginationResult, Paginator
from app.utils.filtering import FilterCondition, QueryFilter

class SolutionOutlineService:
    """Solution Outline service class.
    
    This class provides business logic for managing solution outlines, including versioning.
    """
    
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.solution_outline_repository = solution_outline_repository
        self.project_repository = project_repository
    
    def create_solution_outline(self, project_id: str, content: str, status: SolutionOutlineStatus = SolutionOutlineStatus.draft) -> SolutionOutline:
        """Create a new solution outline with version 1.
        
        Args:
            project_id: The ID of the project.
            content: The content of the solution outline.
            status: The status of the solution outline.
            
        Returns:
            The created solution outline.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Create solution outline
        solution_outline_data = SolutionOutlineCreate(
            project_id=project_id,
            content=content,
            status=status
        )
        
        # Create with version
        return self.solution_outline_repository.create_with_version(self.db, obj_in=solution_outline_data)
    

    def upsert_solution_outline(self, project_id: str, content: str, status: Optional[SolutionOutlineStatus] = None) -> SolutionOutline:
        """Create or update a solution outline, creating a new version if it exists.
        
        This method implements upsert logic - if a solution outline exists for the project,
        it creates a new version. If no solution outline exists, it creates the first version.
        
        Args:
            project_id: The ID of the project.
            content: The content of the solution outline.
            status: The status of the solution outline.
            
        Returns:
            The created or updated solution outline.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Create solution outline with new version (repository handles versioning automatically)
        solution_outline_data = SolutionOutlineCreate(
            project_id=project_id,
            content=content,
            status=status if status is not None else SolutionOutlineStatus.draft
        )
        
        # Create with version (this automatically handles both create and update scenarios)
        return self.solution_outline_repository.create_with_version(self.db, obj_in=solution_outline_data)
    
    def get_latest_solution_outline(self, project_id: str) -> SolutionOutline:
        """Get the latest version of a solution outline.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The latest version of the solution outline, or an empty solution outline if none exists.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Get latest version
        solution_outline = self.solution_outline_repository.get_latest_version(self.db, project_id=project_id)
        if solution_outline is None:
            # Return an empty solution outline object instead of raising an exception
            from datetime import datetime
            from app.api.schemas.solution_outlines import SolutionOutlineResponse
            
            # Create a mock object that behaves like a SolutionOutline model
            class EmptySolutionOutline:
                def __init__(self):
                    self.id = 0
                    self.project_id = project_id
                    self.content = ""
                    self.status = SolutionOutlineStatus.draft
                    self.version = 0
                    self.created_at = datetime.now()
                    self.updated_at = datetime.now()
            
            return EmptySolutionOutline()
        
        return solution_outline
    
    def get_solution_outline_by_version(self, project_id: str, version: int) -> SolutionOutline:
        """Get a specific version of a solution outline.
        
        Args:
            project_id: The ID of the project.
            version: The version number.
            
        Returns:
            The solution outline with the specified version.
            
        Raises:
            NotFoundException: If the project or solution outline version is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Get specific version
        return self.solution_outline_repository.get_by_version_or_404(
            self.db, 
            project_id=project_id, 
            version=version
        )
    
    def get_solution_outline_versions(
        self, 
        project_id: str, 
        pagination: PaginationParams,
        filters: Optional[List[FilterCondition]] = None,
        search: Optional[str] = None
    ) -> PaginationResult[SolutionOutline]:
        """Get all versions of a solution outline with pagination and filtering.
        
        Args:
            project_id: The ID of the project.
            pagination: Pagination parameters.
            filters: List of filter conditions.
            search: Search term.
            
        Returns:
            Paginated result of solution outline versions.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Build base query
        query = self.db.query(SolutionOutline).filter(SolutionOutline.project_id == project_id)
        
        # Apply filters
        if filters:
            allowed_fields = ["version", "status", "created_at", "updated_at"]
            query = QueryFilter.apply_filters(query, filters, SolutionOutline, allowed_fields)
        
        # Apply search
        if search:
            search_fields = ["content"]
            query = QueryFilter.apply_search(query, search, search_fields, SolutionOutline)
        
        # Apply pagination
        allowed_sort_fields = ["version", "created_at", "updated_at"]
        return Paginator.paginate_query(
            query,
            pagination.page,
            pagination.per_page,
            pagination.sort_by,
            pagination.sort_order,
            allowed_sort_fields
        )
    
    def get_solution_outline_version_count(self, project_id: str) -> int:
        """Get the number of versions for a solution outline.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            The number of versions.
            
        Raises:
            NotFoundException: If the project is not found.
        """
        # Check if project exists
        project = self.project_repository.get_or_404(self.db, project_id)
        
        # Get version count
        return self.solution_outline_repository.get_version_count(self.db, project_id=project_id)
    
    def update_solution_outline_status(self, id: int, status: SolutionOutlineStatus) -> SolutionOutline:
        """Update the status of a solution outline.
        
        Args:
            id: The ID of the solution outline.
            status: The new status.
            
        Returns:
            The updated solution outline.
            
        Raises:
            NotFoundException: If the solution outline is not found.
        """
        # Check if solution outline exists
        solution_outline = self.solution_outline_repository.get_or_404(self.db, id)
        
        # Update status
        return self.solution_outline_repository.update_status(self.db, id=id, status=status)
    
    def delete_solution_outline(self, id: int) -> SolutionOutline:
        """Delete a solution outline.
        
        Args:
            id: The ID of the solution outline.
            
        Returns:
            The deleted solution outline.
            
        Raises:
            NotFoundException: If the solution outline is not found.
        """
        # Check if solution outline exists
        solution_outline = self.solution_outline_repository.get_or_404(self.db, id)
        
        # Delete solution outline
        return self.solution_outline_repository.delete(self.db, id=id)
    
    def get_solution_outline_with_review_comments(self, id: int) -> SolutionOutline:
        """Get a solution outline with review comments.
        
        Args:
            id: The ID of the solution outline.
            
        Returns:
            The solution outline with review comments.
            
        Raises:
            NotFoundException: If the solution outline is not found.
        """
        # Get solution outline with review comments
        solution_outline = self.solution_outline_repository.get_with_review_comments(self.db, id=id)
        if solution_outline is None:
            raise NotFoundException(
                f"Solution outline with id {id} not found",
                resource_type="SolutionOutline",
                resource_id=id
            )
        
        return solution_outline

# Create a singleton instance
solution_outline_service = SolutionOutlineService()