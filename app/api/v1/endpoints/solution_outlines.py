"""Solution Outline API endpoints.

This module provides API endpoints for managing solution outlines.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import (
    get_solution_outline_service, 
    get_pagination_params_dependency, 
    get_search_params, 
    get_filter_params
)
from app.services.solution_outlines import SolutionOutlineService
from app.domain.models.solution_outlines import SolutionOutlineStatus
from app.api.schemas.solution_outlines import (
    SolutionOutlineCreate,
    SolutionOutlineUpsert,
    SolutionOutlineResponse,
    SolutionOutlineVersionInfo
)
from app.api.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException, BadRequestException
from app.utils.pagination import PaginationParams
from app.utils.filtering import parse_filter_params
from app.utils.response_utils import paginated_response

router = APIRouter()

@router.post(
    "/projects/{project_id}/solution-outlines",
    response_model=SolutionOutlineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a solution outline",
    description="Create a new solution outline or update an existing one with a new version using upsert logic."
)
def upsert_solution_outline(
    project_id: str = Path(..., description="The ID of the project"),
    content: str = Query(..., description="The content of the solution outline"),
    status: Optional[SolutionOutlineStatus] = Query(
        SolutionOutlineStatus.draft,
        description="The status of the solution outline"
    ),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Create or update a solution outline using upsert logic.
    
    This endpoint implements upsert logic:
    - If no solution outline exists for the project, creates version 1
    - If a solution outline already exists, creates a new version with incremented version number
    
    Args:
        project_id: The ID of the project.
        content: The content of the solution outline.
        status: The status of the solution outline.
        service: The solution outline service.
        
    Returns:
        The created or updated solution outline with version information.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.upsert_solution_outline(project_id, content, status)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get(
    "/projects/{project_id}/solution-outlines/latest",
    response_model=SolutionOutlineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the latest solution outline",
    description="Get the latest version of a solution outline for a project."
)
def get_latest_solution_outline(
    project_id: str = Path(..., description="The ID of the project"),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Get the latest solution outline.
    
    Args:
        project_id: The ID of the project.
        service: The solution outline service.
        
    Returns:
        The latest solution outline.
        
    Raises:
        NotFoundException: If the project or solution outline is not found.
    """
    try:
        return service.get_latest_solution_outline(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/solution-outlines/{version}",
    response_model=SolutionOutlineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a solution outline by version",
    description="Get a specific version of a solution outline for a project."
)
def get_solution_outline_by_version(
    project_id: str = Path(..., description="The ID of the project"),
    version: int = Path(..., description="The version number"),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Get a solution outline by version.
    
    Args:
        project_id: The ID of the project.
        version: The version number.
        service: The solution outline service.
        
    Returns:
        The solution outline with the specified version.
        
    Raises:
        NotFoundException: If the project or solution outline version is not found.
    """
    try:
        return service.get_solution_outline_by_version(project_id, version)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/solution-outlines",
    response_model=PaginatedResponse[SolutionOutlineResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all solution outline versions",
    description="Get all versions of a solution outline for a project with pagination, filtering, and search support."
)
def get_solution_outline_versions(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    search: Optional[str] = Depends(get_search_params),
    filter_params: Dict[str, Any] = Depends(get_filter_params),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Get all solution outline versions with pagination, filtering, and search.
    
    Args:
        request: The FastAPI request object.
        project_id: The ID of the project.
        pagination: Pagination parameters.
        search: Search term.
        filter_params: Filter parameters.
        service: The solution outline service.
        
    Returns:
        Paginated list of solution outline versions.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        # Parse filter conditions
        filters = parse_filter_params(filter_params) if filter_params else None
        
        # Get paginated solution outline versions
        result = service.get_solution_outline_versions(project_id, pagination, filters, search)
        
        # Return paginated response
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="Solution outline versions retrieved successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.patch(
    "/solution-outlines/{id}/status",
    response_model=SolutionOutlineResponse,
    status_code=status.HTTP_200_OK,
    summary="Update solution outline status",
    description="Update the status of a solution outline."
)
def update_solution_outline_status(
    id: int = Path(..., description="The ID of the solution outline"),
    status: SolutionOutlineStatus = Query(..., description="The new status"),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Update solution outline status.
    
    Args:
        id: The ID of the solution outline.
        status: The new status.
        service: The solution outline service.
        
    Returns:
        The updated solution outline.
        
    Raises:
        NotFoundException: If the solution outline is not found.
    """
    try:
        return service.update_solution_outline_status(id, status)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete(
    "/solution-outlines/{id}",
    response_model=SolutionOutlineResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a solution outline",
    description="Delete a solution outline."
)
def delete_solution_outline(
    id: int = Path(..., description="The ID of the solution outline"),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Delete a solution outline.
    
    Args:
        id: The ID of the solution outline.
        service: The solution outline service.
        
    Returns:
        The deleted solution outline.
        
    Raises:
        NotFoundException: If the solution outline is not found.
    """
    try:
        return service.delete_solution_outline(id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/solution-outlines/{id}/with-comments",
    response_model=SolutionOutlineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a solution outline with review comments",
    description="Get a solution outline with its review comments."
)
def get_solution_outline_with_review_comments(
    id: int = Path(..., description="The ID of the solution outline"),
    service: SolutionOutlineService = Depends(get_solution_outline_service)
):
    """Get a solution outline with review comments.
    
    Args:
        id: The ID of the solution outline.
        service: The solution outline service.
        
    Returns:
        The solution outline with review comments.
        
    Raises:
        NotFoundException: If the solution outline is not found.
    """
    try:
        return service.get_solution_outline_with_review_comments(id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)