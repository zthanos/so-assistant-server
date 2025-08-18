"""RequirementItem repository implementation."""

import logging
import time
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.repositories.base import CRUDRepository
from app.domain.models.requirements import RequirementItem, RequirementItemStatus
from app.api.schemas.requirements import RequirementItemCreate, RequirementItemUpdate
from app.core.exceptions import NotFoundException, DatabaseException

logger = logging.getLogger(__name__)


class RequirementItemRepository(CRUDRepository[RequirementItem, RequirementItemCreate, RequirementItemUpdate]):
    """Repository for requirement items with project-specific operations."""
    
    def __init__(self):
        """Initialize the repository with the RequirementItem model."""
        super().__init__(RequirementItem)
    
    def get_by_project(
        self, 
        db: Session,
        project_id: str, 
        status: Optional[RequirementItemStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[RequirementItem]:
        """Get requirement items by project with optional status filtering.
        
        Args:
            project_id: The ID of the project.
            status: Optional status filter.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of requirement items.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        start_time = time.time()
        
        try:
            query = db.query(RequirementItem).filter(
                RequirementItem.project_id == project_id
            )
            
            if status is not None:
                query = query.filter(RequirementItem.status == status)
            
            result = query.order_by(RequirementItem.created_at.desc()).offset(skip).limit(limit).all()
            
            # Log performance metrics
            execution_time = time.time() - start_time
            logger.debug(f"PERFORMANCE: get_by_project query executed in {execution_time:.3f}s - "
                        f"Project: {project_id}, Status: {status}, Skip: {skip}, Limit: {limit}, "
                        f"Results: {len(result)}")
            
            if execution_time > 1.0:  # Log slow queries
                logger.warning(f"SLOW_QUERY: get_by_project took {execution_time:.3f}s - "
                              f"Project: {project_id}, Status: {status}")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Database error in get_by_project after {execution_time:.3f}s: {str(e)}", exc_info=True)
            raise DatabaseException(
                f"Error retrieving requirement items for project {project_id}: {str(e)}", 
                original_exception=e
            )
    
    def get_by_project_and_status(
        self, 
        db: Session,
        project_id: str, 
        statuses: List[RequirementItemStatus],
        skip: int = 0, 
        limit: int = 100
    ) -> List[RequirementItem]:
        """Get requirement items by project and multiple statuses.
        
        Args:
            project_id: The ID of the project.
            statuses: List of statuses to filter by.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of requirement items.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(RequirementItem).filter(
                and_(
                    RequirementItem.project_id == project_id,
                    RequirementItem.status.in_(statuses)
                )
            )
            
            return query.order_by(RequirementItem.created_at.desc()).offset(skip).limit(limit).all()
            
        except Exception as e:
            raise DatabaseException(
                f"Error retrieving requirement items for project {project_id} with statuses {statuses}: {str(e)}", 
                original_exception=e
            )
    
    def count_by_project(
        self, 
        project_id: str, 
        status: Optional[RequirementItemStatus] = None
    ) -> int:
        """Count requirement items by project and optional status.
        
        Args:
            project_id: The ID of the project.
            status: Optional status filter.
            
        Returns:
            Number of requirement items.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(func.count(RequirementItem.id)).filter(
                RequirementItem.project_id == project_id
            )
            
            if status is not None:
                query = query.filter(RequirementItem.status == status)
            
            return query.scalar()
            
        except Exception as e:
            raise DatabaseException(
                f"Error counting requirement items for project {project_id}: {str(e)}", 
                original_exception=e
            )
    
    def count_by_project_and_status(
        self, 
        db: Session,
        project_id: str, 
        status: RequirementItemStatus
    ) -> int:
        """Count requirement items by project and specific status.
        
        Args:
            project_id: The ID of the project.
            status: The status to count.
            
        Returns:
            Number of requirement items with the specified status.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            return db.query(func.count(RequirementItem.id)).filter(
                and_(
                    RequirementItem.project_id == project_id,
                    RequirementItem.status == status
                )
            ).scalar()
            
        except Exception as e:
            raise DatabaseException(
                f"Error counting requirement items for project {project_id} with status {status}: {str(e)}", 
                original_exception=e
            )
    
    def update_status(
        self, 
        db: Session,
        item_id: int, 
        status: RequirementItemStatus
    ) -> RequirementItem:
        """Update requirement item status.
        
        Args:
            item_id: The ID of the requirement item.
            status: The new status.
            
        Returns:
            The updated requirement item.
            
        Raises:
            NotFoundException: If the requirement item is not found.
            DatabaseException: If there's an error with the database operation.
        """
        try:
            item = self.get_or_404(db, item_id)
            item.status = status
            db.commit()
            db.refresh(item)
            return item
            
        except NotFoundException:
            raise
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error updating status for requirement item {item_id}: {str(e)}", 
                original_exception=e
            )
    
    def get_by_project_with_pagination_info(
        self, 
        db: Session,
        project_id: str, 
        status: Optional[RequirementItemStatus] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> tuple[List[RequirementItem], int]:
        """Get requirement items by project with total count for pagination.
        
        Args:
            project_id: The ID of the project.
            status: Optional status filter.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            Tuple of (items, total_count).
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            # Get the items
            items = self.get_by_project(project_id, status, skip, limit)
            
            # Get the total count
            total_count = self.count_by_project(project_id, status)
            
            return items, total_count
            
        except Exception as e:
            raise DatabaseException(
                f"Error retrieving paginated requirement items for project {project_id}: {str(e)}", 
                original_exception=e
            )
    
    def get_status_summary(self, db: Session, project_id: str) -> dict[str, int]:
        """Get a summary of requirement items by status for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            Dictionary with status counts.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            summary = {}
            for status in RequirementItemStatus:
                count = self.count_by_project_and_status(project_id, status)
                summary[status.value] = count
            
            return summary
            
        except Exception as e:
            raise DatabaseException(
                f"Error getting status summary for project {project_id}: {str(e)}", 
                original_exception=e
            )
    
    def search_by_title(
        self, 
        db: Session,
        project_id: str, 
        search_term: str,
        skip: int = 0, 
        limit: int = 100
    ) -> List[RequirementItem]:
        """Search requirement items by title within a project.
        
        Args:
            project_id: The ID of the project.
            search_term: The term to search for in titles.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of matching requirement items.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(RequirementItem).filter(
                and_(
                    RequirementItem.project_id == project_id,
                    RequirementItem.title.ilike(f"%{search_term}%")
                )
            )
            
            return query.order_by(RequirementItem.created_at.desc()).offset(skip).limit(limit).all()
            
        except Exception as e:
            raise DatabaseException(
                f"Error searching requirement items for project {project_id} with term '{search_term}': {str(e)}", 
                original_exception=e
            )
    
    def bulk_update_status(
        self, 
        db: Session,
        item_ids: List[int], 
        status: RequirementItemStatus
    ) -> List[RequirementItem]:
        """Update status for multiple requirement items.
        
        Args:
            item_ids: List of requirement item IDs.
            status: The new status.
            
        Returns:
            List of updated requirement items.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            items = db.query(RequirementItem).filter(
                RequirementItem.id.in_(item_ids)
            ).all()
            
            for item in items:
                item.status = status
            
            db.commit()
            
            # Refresh all items
            for item in items:
                db.refresh(item)
            
            return items
            
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error bulk updating status for requirement items {item_ids}: {str(e)}", 
                original_exception=e
            )
    
    def delete_by_project(self, db: Session, project_id: str) -> int:
        """Delete all requirement items for a project.
        
        Args:
            project_id: The ID of the project.
            
        Returns:
            Number of deleted items.
            
        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            count = db.query(RequirementItem).filter(
                RequirementItem.project_id == project_id
            ).count()
            
            db.query(RequirementItem).filter(
                RequirementItem.project_id == project_id
            ).delete()
            
            db.commit()
            return count
            
        except Exception as e:
            db.rollback()
            raise DatabaseException(
                f"Error deleting requirement items for project {project_id}: {str(e)}", 
                original_exception=e
            )

# Create a singleton instance
requirement_item_repository = RequirementItemRepository()