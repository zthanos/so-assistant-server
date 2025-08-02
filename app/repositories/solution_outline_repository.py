"""Solution Outline repository implementation.

This module provides a repository for SolutionOutline entities.
It extends the base repository and adds solution outline-specific query methods.
"""
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func

from app.repositories.base import CRUDRepository
from app.domain.models.solution_outlines import SolutionOutline, SolutionOutlineStatus
from app.api.schemas.solution_outlines import SolutionOutlineCreate, SolutionOutlineUpdate
from app.core.exceptions import NotFoundException, DatabaseException

class SolutionOutlineRepository(CRUDRepository[SolutionOutline, SolutionOutlineCreate, SolutionOutlineUpdate]):
    """Solution Outline repository class.
    
    This class provides CRUD operations and solution outline-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the SolutionOutline model."""
        super().__init__(SolutionOutline)
    
    def create_with_version(self, db: Session, *, obj_in: SolutionOutlineCreate) -> SolutionOutline:
        """Create a new solution outline with the next version number.
        
        Args:
            db: The database session.
            obj_in: The data to create the solution outline with.
            
        Returns:
            The created solution outline.
        """
        try:
            # Get the latest version for the project
            latest_version = self.get_latest_version_number(db, project_id=obj_in.project_id)
            
            # Create a new version
            new_version = latest_version + 1
            
            # Create the solution outline
            obj_in_data = obj_in.dict() if hasattr(obj_in, "dict") else obj_in
            db_obj = SolutionOutline(**obj_in_data, version=new_version)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except Exception as e:
            db.rollback()
            raise DatabaseException(f"Error creating solution outline: {str(e)}", original_exception=e)
    
    def get_latest_version_number(self, db: Session, *, project_id: str) -> int:
        """Get the latest version number for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The latest version number, or 0 if no versions exist.
        """
        try:
            result = db.query(func.max(SolutionOutline.version)).filter(
                SolutionOutline.project_id == project_id
            ).scalar()
            return result or 0
        except Exception as e:
            raise DatabaseException(f"Error getting latest version number: {str(e)}", original_exception=e)
    
    def get_latest_version(self, db: Session, *, project_id: str) -> Optional[SolutionOutline]:
        """Get the latest version of a solution outline for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The latest version of the solution outline if found, None otherwise.
        """
        try:
            return db.query(SolutionOutline).filter(
                SolutionOutline.project_id == project_id
            ).order_by(desc(SolutionOutline.version)).first()
        except Exception as e:
            raise DatabaseException(f"Error getting latest version: {str(e)}", original_exception=e)
    
    def get_by_version(self, db: Session, *, project_id: str, version: int) -> Optional[SolutionOutline]:
        """Get a specific version of a solution outline for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            version: The version number.
            
        Returns:
            The solution outline if found, None otherwise.
        """
        try:
            return db.query(SolutionOutline).filter(
                SolutionOutline.project_id == project_id,
                SolutionOutline.version == version
            ).first()
        except Exception as e:
            raise DatabaseException(f"Error getting version {version}: {str(e)}", original_exception=e)
    
    def get_by_version_or_404(self, db: Session, *, project_id: str, version: int) -> SolutionOutline:
        """Get a specific version of a solution outline for a project or raise a 404 exception.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            version: The version number.
            
        Returns:
            The solution outline if found.
            
        Raises:
            NotFoundException: If the solution outline is not found.
        """
        solution_outline = self.get_by_version(db, project_id=project_id, version=version)
        if solution_outline is None:
            raise NotFoundException(
                f"Solution outline with version {version} not found for project {project_id}",
                resource_type="SolutionOutline"
            )
        return solution_outline
    
    def get_all_versions(self, db: Session, *, project_id: str, skip: int = 0, limit: int = 100) -> List[SolutionOutline]:
        """Get all versions of a solution outline for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of solution outlines.
        """
        try:
            return db.query(SolutionOutline).filter(
                SolutionOutline.project_id == project_id
            ).order_by(desc(SolutionOutline.version)).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting all versions: {str(e)}", original_exception=e)
    
    def get_version_count(self, db: Session, *, project_id: str) -> int:
        """Get the number of versions for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            
        Returns:
            The number of versions.
        """
        try:
            return db.query(func.count(SolutionOutline.id)).filter(
                SolutionOutline.project_id == project_id
            ).scalar()
        except Exception as e:
            raise DatabaseException(f"Error getting version count: {str(e)}", original_exception=e)
    
    def get_by_status(
        self, db: Session, *, project_id: str, status: SolutionOutlineStatus, skip: int = 0, limit: int = 100
    ) -> List[SolutionOutline]:
        """Get solution outlines by status for a project.
        
        Args:
            db: The database session.
            project_id: The ID of the project.
            status: The solution outline status.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of solution outlines with the specified status.
        """
        try:
            return db.query(SolutionOutline).filter(
                SolutionOutline.project_id == project_id,
                SolutionOutline.status == status
            ).order_by(desc(SolutionOutline.version)).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting solution outlines by status: {str(e)}", original_exception=e)
    
    def update_status(self, db: Session, *, id: int, status: SolutionOutlineStatus) -> SolutionOutline:
        """Update the status of a solution outline.
        
        Args:
            db: The database session.
            id: The ID of the solution outline.
            status: The new status.
            
        Returns:
            The updated solution outline.
        """
        return self.update_by_id(db, id=id, obj_in={"status": status})
    
    def get_with_review_comments(self, db: Session, *, id: int) -> Optional[SolutionOutline]:
        """Get a solution outline with review comments loaded.
        
        Args:
            db: The database session.
            id: The ID of the solution outline.
            
        Returns:
            The solution outline with review comments if found, None otherwise.
        """
        try:
            return db.query(SolutionOutline).filter(
                SolutionOutline.id == id
            ).options(
                joinedload(SolutionOutline.review_comments)
            ).first()
        except Exception as e:
            raise DatabaseException(f"Error getting solution outline with review comments: {str(e)}", original_exception=e)

# Create a singleton instance
solution_outline_repository = SolutionOutlineRepository()