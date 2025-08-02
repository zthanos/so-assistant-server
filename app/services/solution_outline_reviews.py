"""Solution Outline Review service implementation.

This module provides a service for managing LLM reviews of solution outlines.
It follows the service pattern and provides a clean interface for review operations.
"""
from typing import List, Optional, Dict, Any, AsyncGenerator, Tuple
from sqlalchemy.orm import Session
from fastapi import Depends, BackgroundTasks

from app.core.database import get_db
from app.repositories.solution_outline_repository import solution_outline_repository
from app.repositories.review_comment_repository import review_comment_repository
from app.domain.models.review_comments import ReviewComment, ReviewCommentStatus
from app.api.schemas.review_comments import ReviewCommentCreate, ReviewCommentUpdate, ReviewCommentResponse
from app.core.exceptions import NotFoundException, LLMException
from app.services.llm.client import StreamingOllamaClient
from app.core.events import SSEManager

class SolutionOutlineReviewService:
    """Solution Outline Review service class.
    
    This class provides business logic for managing LLM reviews of solution outlines,
    including streaming review generation.
    """
    
    def __init__(
        self, 
        db: Session = Depends(get_db),
        sse_manager: Optional[SSEManager] = None,
        ollama_client: Optional[StreamingOllamaClient] = None
    ):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
            sse_manager: Optional SSE manager for streaming.
            ollama_client: Optional Ollama client for LLM integration.
        """
        self.db = db
        self.solution_outline_repository = solution_outline_repository
        self.review_comment_repository = review_comment_repository
        self.sse_manager = sse_manager
        self.ollama_client = ollama_client or StreamingOllamaClient()
    
    async def create_review(
        self, 
        solution_outline_id: int,
        client_id: Optional[str] = None
    ) -> AsyncGenerator[ReviewComment, None]:
        """Create a new review for a solution outline, streaming the results.
        
        Args:
            solution_outline_id: The ID of the solution outline.
            client_id: Optional client ID for SSE streaming.
            
        Yields:
            Review comments as they are generated.
            
        Raises:
            NotFoundException: If the solution outline is not found.
            LLMException: If there's an error with the LLM.
        """
        # Check if solution outline exists
        solution_outline = self.solution_outline_repository.get_or_404(self.db, solution_outline_id)
        
        # Generate prompt for LLM
        prompt = self._generate_review_prompt(solution_outline.content)
        
        # Stream LLM response and create review comments
        current_comment = ""
        comment_count = 0
        
        try:
            # Send start event if client_id is provided
            if client_id and self.sse_manager:
                await self.sse_manager.send_event(
                    client_id,
                    "review.start",
                    {
                        "message": "Starting solution outline review",
                        "solution_outline_id": solution_outline_id
                    }
                )
            
            # Stream LLM response
            async for chunk in self.ollama_client.generate_stream(prompt, prompt_key="solution_outline_review"):
                # Process chunk to extract comments
                current_comment, comments = self._process_review_chunk(current_comment + chunk)
                
                # Create and yield comments
                for comment_text in comments:
                    comment_count += 1
                    comment = self._create_review_comment(solution_outline_id, comment_text)
                    
                    # Send comment event if client_id is provided
                    if client_id and self.sse_manager:
                        await self.sse_manager.send_event(
                            client_id,
                            "review.comment",
                            {
                                "comment": ReviewCommentResponse.from_orm(comment).dict(),
                                "solution_outline_id": solution_outline_id
                            }
                        )
                    
                    yield comment
            
            # Process any remaining comment
            if current_comment.strip():
                comment = self._create_review_comment(solution_outline_id, current_comment)
                
                # Send comment event if client_id is provided
                if client_id and self.sse_manager:
                    await self.sse_manager.send_event(
                        client_id,
                        "review.comment",
                        {
                            "comment": ReviewCommentResponse.from_orm(comment).dict(),
                            "solution_outline_id": solution_outline_id
                        }
                    )
                
                yield comment
            
            # Send complete event if client_id is provided
            if client_id and self.sse_manager:
                await self.sse_manager.send_event(
                    client_id,
                    "review.complete",
                    {
                        "message": "Solution outline review complete",
                        "solution_outline_id": solution_outline_id,
                        "comment_count": comment_count
                    }
                )
                
        except Exception as e:
            # Send error event if client_id is provided
            if client_id and self.sse_manager:
                try:
                    await self.sse_manager.send_event(
                        client_id,
                        "review.error",
                        {
                            "message": str(e),
                            "solution_outline_id": solution_outline_id,
                            "error_type": "llm_error" if isinstance(e, LLMException) else "unexpected_error"
                        }
                    )
                except Exception:
                    pass
            
            # Re-raise the exception
            raise
    
    def get_review_comments(
        self, 
        solution_outline_id: int, 
        skip: int = 0, 
        limit: int = 100
    ) -> List[ReviewComment]:
        """Get all review comments for a solution outline.
        
        Args:
            solution_outline_id: The ID of the solution outline.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of review comments.
        """
        return self.review_comment_repository.get_by_solution_outline(
            self.db, 
            solution_outline_id=solution_outline_id, 
            skip=skip, 
            limit=limit
        )
    
    def get_review_comments_by_status(
        self, 
        solution_outline_id: int, 
        status: ReviewCommentStatus,
        skip: int = 0, 
        limit: int = 100
    ) -> List[ReviewComment]:
        """Get review comments by status for a solution outline.
        
        Args:
            solution_outline_id: The ID of the solution outline.
            status: The review comment status.
            skip: The number of records to skip.
            limit: The maximum number of records to return.
            
        Returns:
            A list of review comments with the specified status.
        """
        return self.review_comment_repository.get_by_status(
            self.db, 
            solution_outline_id=solution_outline_id, 
            status=status,
            skip=skip, 
            limit=limit
        )
    
    def update_comment_status(self, comment_id: int, status: ReviewCommentStatus) -> ReviewComment:
        """Update the status of a review comment.
        
        Args:
            comment_id: The ID of the review comment.
            status: The new status.
            
        Returns:
            The updated review comment.
            
        Raises:
            NotFoundException: If the review comment is not found.
        """
        # Check if review comment exists
        comment = self.review_comment_repository.get_or_404(self.db, comment_id)
        
        # Update status
        return self.review_comment_repository.update_status(self.db, id=comment_id, status=status)
    
    def bulk_update_comment_status(self, comment_ids: List[int], status: ReviewCommentStatus) -> List[ReviewComment]:
        """Update the status of multiple review comments.
        
        Args:
            comment_ids: The IDs of the review comments.
            status: The new status.
            
        Returns:
            The updated review comments.
        """
        return self.review_comment_repository.bulk_update_status(self.db, ids=comment_ids, status=status)
    
    def get_status_counts(self, solution_outline_id: int) -> Dict[ReviewCommentStatus, int]:
        """Get the count of review comments by status for a solution outline.
        
        Args:
            solution_outline_id: The ID of the solution outline.
            
        Returns:
            A dictionary mapping status to count.
        """
        return self.review_comment_repository.get_status_counts(self.db, solution_outline_id=solution_outline_id)
    
    def _create_review_comment(self, solution_outline_id: int, content: str) -> ReviewComment:
        """Create a review comment.
        
        Args:
            solution_outline_id: The ID of the solution outline.
            content: The content of the review comment.
            
        Returns:
            The created review comment.
        """
        comment_data = ReviewCommentCreate(
            solution_outline_id=solution_outline_id,
            content=content,
            status=ReviewCommentStatus.pending
        )
        
        return self.review_comment_repository.create(self.db, obj_in=comment_data)
    
    def _generate_review_prompt(self, solution_outline_content: str) -> str:
        """Generate a prompt for the LLM to review a solution outline.
        
        Args:
            solution_outline_content: The content of the solution outline.
            
        Returns:
            The generated prompt.
        """
        return f"""
        You are a senior software architect reviewing a solution outline document.
        Please review the following solution outline and provide specific, actionable feedback.
        Focus on:
        1. Architecture and design issues
        2. Potential scalability or performance concerns
        3. Security considerations
        4. Missing components or requirements
        5. Clarity and completeness of the design

        For each issue you identify, provide a clear explanation of the problem and a suggestion for improvement.
        Format each issue as a separate, self-contained comment.
        
        Solution Outline:
        {solution_outline_content}
        
        Please provide your review comments:
        """
    
    def _process_review_chunk(self, text: str) -> Tuple[str, List[str]]:
        """Process a chunk of review text to extract comments.
        
        This method attempts to identify complete comments in the streaming text.
        It uses heuristics to determine comment boundaries.
        
        Args:
            text: The current accumulated text.
            
        Returns:
            A tuple containing the remaining text and a list of complete comments.
        """
        # Simple heuristic: Split on numbered items or clear paragraph breaks
        # This is a simplified approach and might need refinement based on actual LLM output patterns
        
        # Look for common comment patterns
        patterns = [
            "\n\d+\.", "\n\n", "\nIssue \d+:", "\nComment \d+:", "\nFeedback \d+:"
        ]
        
        remaining_text = text
        comments = []
        
        # Try to extract complete comments
        for pattern in patterns:
            if pattern in remaining_text:
                parts = remaining_text.split(pattern)
                if len(parts) > 1:
                    # First part might be a complete comment
                    if parts[0].strip():
                        comments.append(parts[0].strip())
                    
                    # Reassemble the remaining text
                    remaining_text = pattern + pattern.join(parts[1:])
                    
                    # If we found comments with this pattern, don't try other patterns
                    if comments:
                        break
        
        return remaining_text, comments

# Create a singleton instance
solution_outline_review_service = SolutionOutlineReviewService()