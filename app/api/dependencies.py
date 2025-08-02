"""FastAPI dependencies.

This module provides FastAPI dependency functions for the application.
These dependencies are used to inject services, repositories, and other
components into API endpoints.
"""
from typing import Tuple, Optional, Dict, Any
from fastapi import Depends, Request, BackgroundTasks, Query
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from app.core.database import get_db
from app.core.events import SSEManager
from app.utils.pagination import PaginationParams, get_pagination_params
from app.utils.filtering import FilterCondition, parse_filter_params

# Global SSE manager instance
_sse_manager = SSEManager()

def get_sse_manager() -> SSEManager:
    """Get the SSE manager instance.
    
    Returns:
        The global SSE manager instance
    """
    return _sse_manager

async def get_sse_connection(
    request: Request,
    client_type: str = "generic",
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Tuple[str, EventSourceResponse]:
    """Create an SSE connection.
    
    This dependency function creates a new SSE connection and returns
    the client ID and EventSourceResponse.
    
    Args:
        request: The FastAPI request object
        client_type: Type of client for categorization purposes
        sse_manager: The SSE manager instance
        
    Returns:
        A tuple containing the client ID and the EventSourceResponse
    """
    return await sse_manager.register_client(request, client_type)

def cleanup_stale_sse_connections(
    background_tasks: BackgroundTasks,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> None:
    """Clean up stale SSE connections.
    
    This dependency function cleans up stale SSE connections.
    
    Args:
        background_tasks: FastAPI BackgroundTasks for async cleanup
        sse_manager: The SSE manager instance
    """
    sse_manager.cleanup_stale_connections(background_tasks)

# Service dependencies
def get_llm_streaming_service(sse_manager: SSEManager = Depends(get_sse_manager)):
    """Get the LLM streaming service.
    
    Args:
        sse_manager: The SSE manager instance
        
    Returns:
        The LLM streaming service instance
    """
    from app.services.llm import LLMStreamingService
    return LLMStreamingService(sse_manager)

def get_ollama_client():
    """Get the Ollama client.
    
    Returns:
        The Ollama client instance
    """
    from app.services.llm import StreamingOllamaClient
    return StreamingOllamaClient()

# Repository dependencies
def get_project_repository(db: Session = Depends(get_db)):
    """Get the project repository.
    
    Args:
        db: The database session
        
    Returns:
        The project repository instance
    """
    from app.repositories.project_repository import ProjectRepository
    return ProjectRepository(db)

def get_solution_outline_repository(db: Session = Depends(get_db)):
    """Get the solution outline repository.
    
    Args:
        db: The database session
        
    Returns:
        The solution outline repository instance
    """
    from app.repositories.solution_outline_repository import SolutionOutlineRepository
    return SolutionOutlineRepository(db)

def get_adr_repository(db: Session = Depends(get_db)):
    """Get the ADR repository.
    
    Args:
        db: The database session
        
    Returns:
        The ADR repository instance
    """
    from app.repositories.adr_repository import ADRRepository
    return ADRRepository(db)

def get_review_comment_repository(db: Session = Depends(get_db)):
    """Get the review comment repository.
    
    Args:
        db: The database session
        
    Returns:
        The review comment repository instance
    """
    from app.repositories.review_comment_repository import ReviewCommentRepository
    return ReviewCommentRepository(db)

def get_team_repository(db: Session = Depends(get_db)):
    """Get the team repository.
    
    Args:
        db: The database session
        
    Returns:
        The team repository instance
    """
    from app.repositories.team_repository import TeamRepository
    return TeamRepository(db)

def get_task_repository(db: Session = Depends(get_db)):
    """Get the task repository.
    
    Args:
        db: The database session
        
    Returns:
        The task repository instance
    """
    from app.repositories.task_repository import TaskRepository
    return TaskRepository(db)

def get_solution_outline_service(db: Session = Depends(get_db)):
    """Get the solution outline service.
    
    Args:
        db: The database session
        
    Returns:
        The solution outline service instance
    """
    from app.services.solution_outlines import SolutionOutlineService
    return SolutionOutlineService(db)

def get_solution_outline_review_service(
    db: Session = Depends(get_db),
    sse_manager: SSEManager = Depends(get_sse_manager)
):
    """Get the solution outline review service.
    
    Args:
        db: The database session
        sse_manager: The SSE manager instance
        
    Returns:
        The solution outline review service instance
    """
    from app.services.solution_outline_reviews import SolutionOutlineReviewService
    return SolutionOutlineReviewService(db, sse_manager)

def get_adr_service(db: Session = Depends(get_db)):
    """Get the ADR service.
    
    Args:
        db: The database session
        
    Returns:
        The ADR service instance
    """
    from app.services.adrs import ADRService
    return ADRService(db)

def get_team_service(db: Session = Depends(get_db)):
    """Get the team service.
    
    Args:
        db: The database session
        
    Returns:
        The team service instance
    """
    from app.services.teams import TeamService
    return TeamService(db)

def get_task_service(db: Session = Depends(get_db)):
    """Get the task service.
    
    Args:
        db: The database session
        
    Returns:
        The task service instance
    """
    from app.services.tasks import TaskService
    return TaskService(db)

# Pagination and filtering dependencies
def get_pagination_params_dependency(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: Optional[str] = Query(None, description="Field to sort by"),
    sort_order: str = Query("asc", regex="^(asc|desc)$", description="Sort order (asc/desc)")
) -> PaginationParams:
    """Get pagination parameters from query parameters.
    
    Args:
        page: Page number (1-based)
        per_page: Items per page
        sort_by: Field to sort by
        sort_order: Sort order (asc/desc)
        
    Returns:
        PaginationParams object
    """
    return get_pagination_params(page, per_page, sort_by, sort_order)

def get_search_params(
    search: Optional[str] = Query(None, description="Search term")
) -> Optional[str]:
    """Get search parameters from query parameters.
    
    Args:
        search: Search term
        
    Returns:
        Search term or None
    """
    return search

def get_filter_params(
    request: Request
) -> Dict[str, Any]:
    """Get filter parameters from query parameters.
    
    This dependency extracts filter parameters from the request query parameters.
    Filter parameters should follow the format: field__operator=value
    
    Examples:
    - name=John -> {"name": "John"}
    - age__gte=18 -> {"age__gte": 18}
    - status__in=active,pending -> {"status__in": ["active", "pending"]}
    
    Args:
        request: FastAPI request object
        
    Returns:
        Dictionary of filter parameters
    """
    filter_params = {}
    
    # Get all query parameters
    for key, value in request.query_params.items():
        # Skip pagination and search parameters
        if key in ["page", "per_page", "sort_by", "sort_order", "search"]:
            continue
            
        # Handle comma-separated values for 'in' and 'not_in' operators
        if "__in" in key or "__not_in" in key:
            filter_params[key] = value.split(",") if value else []
        else:
            filter_params[key] = value
    
    return filter_params