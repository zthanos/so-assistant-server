"""Solution Outline Review API endpoints.

This module provides API endpoints for managing solution outline reviews.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.api.dependencies import get_solution_outline_review_service, get_sse_connection
from app.services.solution_outline_reviews import SolutionOutlineReviewService
from app.domain.models.review_comments import ReviewCommentStatus
from app.api.schemas.review_comments import (
    ReviewCommentResponse,
    ReviewCommentUpdate
)
from app.core.exceptions import NotFoundException, LLMException

router = APIRouter()

@router.post(
    "/solution-outlines/{solution_outline_id}/review",
    response_class=EventSourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Create a new review for a solution outline",
    description="Create a new review for a solution outline, streaming the results using SSE."
)
async def create_review(
    solution_outline_id: int = Path(..., description="The ID of the solution outline"),
    request: Request = None,
    background_tasks: BackgroundTasks = None,
    client_id_and_sse: tuple = Depends(get_sse_connection),
    service: SolutionOutlineReviewService = Depends(get_solution_outline_review_service)
):
    """Create a new review for a solution outline.
    
    Args:
        solution_outline_id: The ID of the solution outline.
        request: The FastAPI request object.
        background_tasks: FastAPI BackgroundTasks for async cleanup.
        client_id_and_sse: A tuple containing the client ID and EventSourceResponse.
        service: The solution outline review service.
        
    Returns:
        An EventSourceResponse for streaming the review results.
        
    Raises:
        NotFoundException: If the solution outline is not found.
        LLMException: If there's an error with the LLM.
    """
    client_id, sse = client_id_and_sse
    
    # Start the review process in the background
    async def review_generator():
        try:
            async for _ in service.create_review(solution_outline_id, client_id):
                pass
        except NotFoundException as e:
            # The error will be sent as an SSE event
            pass
        except LLMException as e:
            # The error will be sent as an SSE event
            pass
        except Exception as e:
            # The error will be sent as an SSE event
            pass
    
    # Add the review generator to background tasks
    background_tasks.add_task(review_generator)
    
    # Return the SSE response
    return sse

@router.get(
    "/solution-outlines/{solution_outline_id}/review-comments",
    response_model=List[ReviewCommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get review comments for a solution outline",
    description="Get all review comments for a solution outline."
)
def get_review_comments(
    solution_outline_id: int = Path(..., description="The ID of the solution outline"),
    status: Optional[ReviewCommentStatus] = Query(
        None,
        description="Filter comments by status"
    ),
    skip: int = Query(0, description="The number of records to skip"),
    limit: int = Query(100, description="The maximum number of records to return"),
    service: SolutionOutlineReviewService = Depends(get_solution_outline_review_service)
):
    """Get review comments for a solution outline.
    
    Args:
        solution_outline_id: The ID of the solution outline.
        status: Optional filter for comment status.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        service: The solution outline review service.
        
    Returns:
        A list of review comments.
    """
    try:
        if status is not None:
            return service.get_review_comments_by_status(solution_outline_id, status, skip, limit)
        else:
            return service.get_review_comments(solution_outline_id, skip, limit)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch(
    "/review-comments/{comment_id}/status",
    response_model=ReviewCommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update review comment status",
    description="Update the status of a review comment."
)
def update_comment_status(
    comment_id: int = Path(..., description="The ID of the review comment"),
    status_update: ReviewCommentUpdate = None,
    service: SolutionOutlineReviewService = Depends(get_solution_outline_review_service)
):
    """Update review comment status.
    
    Args:
        comment_id: The ID of the review comment.
        status_update: The new status.
        service: The solution outline review service.
        
    Returns:
        The updated review comment.
        
    Raises:
        NotFoundException: If the review comment is not found.
    """
    try:
        return service.update_comment_status(comment_id, status_update.status)
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.patch(
    "/solution-outlines/{solution_outline_id}/review-comments/bulk-status",
    response_model=List[ReviewCommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Bulk update review comment status",
    description="Update the status of multiple review comments."
)
def bulk_update_comment_status(
    solution_outline_id: int = Path(..., description="The ID of the solution outline"),
    comment_ids: List[int] = Query(..., description="The IDs of the review comments"),
    status: ReviewCommentStatus = Query(..., description="The new status"),
    service: SolutionOutlineReviewService = Depends(get_solution_outline_review_service)
):
    """Bulk update review comment status.
    
    Args:
        solution_outline_id: The ID of the solution outline.
        comment_ids: The IDs of the review comments.
        status: The new status.
        service: The solution outline review service.
        
    Returns:
        The updated review comments.
    """
    try:
        return service.bulk_update_comment_status(comment_ids, status)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get(
    "/solution-outlines/{solution_outline_id}/review-comments/status-counts",
    status_code=status.HTTP_200_OK,
    summary="Get review comment status counts",
    description="Get the count of review comments by status for a solution outline."
)
def get_status_counts(
    solution_outline_id: int = Path(..., description="The ID of the solution outline"),
    service: SolutionOutlineReviewService = Depends(get_solution_outline_review_service)
):
    """Get review comment status counts.
    
    Args:
        solution_outline_id: The ID of the solution outline.
        service: The solution outline review service.
        
    Returns:
        A dictionary mapping status to count.
    """
    try:
        counts = service.get_status_counts(solution_outline_id)
        # Convert enum keys to strings for JSON serialization
        return {status.name: count for status, count in counts.items()}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))