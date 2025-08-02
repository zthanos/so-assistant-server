"""Review Comment repository implementation.

This module provides a repository for ReviewComment entities.
It extends the base repository and adds review comment-specific query methods.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.repositories.base import CRUDRepository
from app.domain.models.review_comments import ReviewComment, ReviewCommentStatus
from app.api.schemas.review_comments import ReviewCommentCreate, ReviewCommentUpdate
from app.core.exceptions import NotFoundException, DatabaseException

class ReviewCommentRepository(CRUDRepository[ReviewComment, ReviewCommentCreate, ReviewCommentUpdate]):
    """Review Comment repository class.
    
    This class provides CRUD operations and review comment-specific query methods.
    """
    
    def __init__(self):
        """Initialize the repository with the ReviewComment model."""
        super().__init__(ReviewComment)
    
    def get_by_solution_outline(
        self, db: Session, *, solution_outline_id: int, skip: int = 0, limit: int = 100
    ) -> List[ReviewComment]:
        """Get review comments for a solution outline.
        
        Args:
            db: The database session.
            solution_outline_id: The ID of the solution outline.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of review comments for the solution outline.
        """
        return self.get_multi_by_field(db, "solution_outline_id", solution_outline_id, skip=skip, limit=limit)
    
    def get_by_status(
        self, db: Session, *, solution_outline_id: int, status: ReviewCommentStatus, skip: int = 0, limit: int = 100
    ) -> List[ReviewComment]:
        """Get review comments by status for a solution outline.
        
        Args:
            db: The database session.
            solution_outline_id: The ID of the solution outline.
            status: The review comment status.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of review comments with the specified status.
        """
        try:
            return db.query(self.model).filter(
                self.model.solution_outline_id == solution_outline_id,
                self.model.status == status
            ).offset(skip).limit(limit).all()
        except Exception as e:
            raise DatabaseException(f"Error getting review comments by status: {str(e)}", original_exception=e)
    
    def update_status(self, db: Session, *, id: int, status: ReviewCommentStatus) -> ReviewComment:
        """Update the status of a review comment.
        
        Args:
            db: The database session.
            id: The ID of the review comment.
            status: The new status.
            
        Returns:
            The updated review comment.
        """
        return self.update_by_id(db, id=id, obj_in={"status": status})
    
    def bulk_update_status(
        self, db: Session, *, ids: List[int], status: ReviewCommentStatus
    ) -> List[ReviewComment]:
        """Update the status of multiple review comments.
        
        Args:
            db: The database session.
            ids: The IDs of the review comments.
            status: The new status.
            
        Returns:
            The updated review comments.
        """
        return self.bulk_update(db, ids=ids, obj_in={"status": status})
    
    def count_by_solution_outline(self, db: Session, *, solution_outline_id: int) -> int:
        """Count the number of review comments for a solution outline.
        
        Args:
            db: The database session.
            solution_outline_id: The ID of the solution outline.
            
        Returns:
            The number of review comments for the solution outline.
        """
        try:
            return db.query(self.model).filter(
                self.model.solution_outline_id == solution_outline_id
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting review comments: {str(e)}", original_exception=e)
    
    def count_by_status(self, db: Session, *, solution_outline_id: int, status: ReviewCommentStatus) -> int:
        """Count the number of review comments with a specific status for a solution outline.
        
        Args:
            db: The database session.
            solution_outline_id: The ID of the solution outline.
            status: The review comment status.
            
        Returns:
            The number of review comments with the specified status.
        """
        try:
            return db.query(self.model).filter(
                self.model.solution_outline_id == solution_outline_id,
                self.model.status == status
            ).count()
        except Exception as e:
            raise DatabaseException(f"Error counting review comments by status: {str(e)}", original_exception=e)
    
    def get_status_counts(self, db: Session, *, solution_outline_id: int) -> Dict[ReviewCommentStatus, int]:
        """Get the count of review comments by status for a solution outline.
        
        Args:
            db: The database session.
            solution_outline_id: The ID of the solution outline.
            
        Returns:
            A dictionary mapping status to count.
        """
        try:
            counts = {}
            for status in ReviewCommentStatus:
                counts[status] = self.count_by_status(db, solution_outline_id=solution_outline_id, status=status)
            return counts
        except Exception as e:
            raise DatabaseException(f"Error getting status counts: {str(e)}", original_exception=e)

# Create a singleton instance
review_comment_repository = ReviewCommentRepository()