"""Architecture Decision Record (ADR) API endpoints.

This module provides API endpoints for managing Architecture Decision Records (ADRs).
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import (
    get_adr_service, 
    get_pagination_params_dependency, 
    get_search_params, 
    get_filter_params
)
from app.services.adrs import ADRService
from app.api.schemas.adrs import ADRCreate, ADRUpdate, ADRUpsert, ADRResponse
from app.api.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams
from app.utils.filtering import parse_filter_params
from app.utils.response_utils import paginated_response

router = APIRouter(tags=["ADRs"])

@router.post(
    "/projects/{project_id}/adrs",
    response_model=ADRResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update an ADR (upsert)",
    description="Create a new ADR or update an existing one. If adr_id is provided in the request body, the ADR will be updated; otherwise, a new ADR will be created."
)
def upsert_adr(
    project_id: str = Path(..., description="The ID of the project"),
    adr_data: ADRUpsert = ...,
    service: ADRService = Depends(get_adr_service)
):
    """Create or update an ADR (upsert operation).
    
    Args:
        project_id: The ID of the project.
        adr_data: The ADR data containing title, content, and optional adr_id.
        service: The ADR service.
        
    Returns:
        The created or updated ADR.
        
    Raises:
        NotFoundException: If the project or ADR (for update) is not found.
        ConflictException: If an ADR with the same title already exists for the project.
    """
    try:
        return service.upsert_adr(project_id, adr_data)
    except (NotFoundException, ConflictException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/adrs/{adr_id}",
    response_model=ADRResponse,
    status_code=status.HTTP_200_OK,
    summary="Get an ADR by ID",
    description="Get an Architecture Decision Record (ADR) by its ID."
)
def get_adr(
    adr_id: int = Path(..., description="The ID of the ADR"),
    service: ADRService = Depends(get_adr_service)
):
    """Get an ADR by ID.
    
    Args:
        adr_id: The ID of the ADR.
        service: The ADR service.
        
    Returns:
        The ADR.
        
    Raises:
        NotFoundException: If the ADR is not found.
    """
    try:
        return service.get_adr(adr_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/adrs",
    response_model=PaginatedResponse[ADRResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all ADRs for a project",
    description="Get all Architecture Decision Records (ADRs) for a project with pagination, filtering, and search support."
)
def get_adrs_for_project(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    search: Optional[str] = Depends(get_search_params),
    filter_params: Dict[str, Any] = Depends(get_filter_params),
    service: ADRService = Depends(get_adr_service)
):
    """Get all ADRs for a project with pagination, filtering, and search.
    
    Args:
        request: The FastAPI request object.
        project_id: The ID of the project.
        pagination: Pagination parameters.
        search: Search term.
        filter_params: Filter parameters.
        service: The ADR service.
        
    Returns:
        Paginated list of ADRs for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        # Parse filter conditions
        filters = parse_filter_params(filter_params) if filter_params else None
        
        # Get paginated ADRs
        result = service.get_adrs_for_project(project_id, pagination, filters, search)
        
        # Return paginated response
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="ADRs retrieved successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)



@router.delete(
    "/adrs/{adr_id}",
    response_model=ADRResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete an ADR",
    description="Delete an Architecture Decision Record (ADR)."
)
def delete_adr(
    adr_id: int = Path(..., description="The ID of the ADR"),
    service: ADRService = Depends(get_adr_service)
):
    """Delete an ADR.
    
    Args:
        adr_id: The ID of the ADR.
        service: The ADR service.
        
    Returns:
        The deleted ADR.
        
    Raises:
        NotFoundException: If the ADR is not found.
    """
    try:
        return service.delete_adr(adr_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/adrs/search",
    response_model=PaginatedResponse[ADRResponse],
    status_code=status.HTTP_200_OK,
    summary="Search ADRs",
    description="Search Architecture Decision Records (ADRs) by title or content for a project with pagination support."
)
def search_adrs(
    project_id: str = Path(..., description="The ID of the project"),
    query: str = Query(..., description="The search query"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    service: ADRService = Depends(get_adr_service)
):
    """Search ADRs with pagination support.
    
    Args:
        project_id: The ID of the project.
        query: The search query.
        pagination: Pagination parameters.
        service: The ADR service.
        
    Returns:
        Paginated list of ADRs matching the search query.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        result = service.search_adrs(project_id, query, pagination)
        
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="ADRs search completed successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/adrs/recent",
    response_model=List[ADRResponse],
    status_code=status.HTTP_200_OK,
    summary="Get recent ADRs",
    description="Get recent Architecture Decision Records (ADRs) for a project."
)
def get_recent_adrs(
    project_id: str = Path(..., description="The ID of the project"),
    limit: int = Query(5, description="The maximum number of records to return"),
    service: ADRService = Depends(get_adr_service)
):
    """Get recent ADRs.
    
    Args:
        project_id: The ID of the project.
        limit: The maximum number of records to return.
        service: The ADR service.
        
    Returns:
        A list of recent ADRs for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.get_recent_adrs(project_id, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/adrs/count",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Count ADRs for a project",
    description="Count the number of Architecture Decision Records (ADRs) for a project."
)
def count_adrs_for_project(
    project_id: str = Path(..., description="The ID of the project"),
    service: ADRService = Depends(get_adr_service)
):
    """Count ADRs for a project.
    
    Args:
        project_id: The ID of the project.
        service: The ADR service.
        
    Returns:
        The number of ADRs for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.count_adrs_for_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

# Endpoint for linking ADRs to solution outlines
@router.post(
    "/solution-outlines/{solution_outline_id}/adrs/{adr_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Link an ADR to a solution outline",
    description="Link an Architecture Decision Record (ADR) to a solution outline."
)
def link_adr_to_solution_outline(
    solution_outline_id: int = Path(..., description="The ID of the solution outline"),
    adr_id: int = Path(..., description="The ID of the ADR"),
    service: ADRService = Depends(get_adr_service)
):
    """Link an ADR to a solution outline.
    
    This is a placeholder endpoint for linking ADRs to solution outlines.
    The actual implementation would require additional service methods and
    possibly a new relationship table in the database.
    
    Args:
        solution_outline_id: The ID of the solution outline.
        adr_id: The ID of the ADR.
        service: The ADR service.
        
    Raises:
        NotFoundException: If the solution outline or ADR is not found.
    """
    # This is a placeholder for the actual implementation
    # The actual implementation would require additional service methods
    # and possibly a new relationship table in the database
    return {"message": "Not implemented yet"}