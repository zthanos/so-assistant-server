"""Team API endpoints.

This module provides API endpoints for managing teams.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Body, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import (
    get_team_service, 
    get_pagination_params_dependency, 
    get_search_params, 
    get_filter_params
)
from app.services.teams import TeamService
from app.api.schemas.teams import TeamBase, TeamCreate, TeamUpdate, TeamResponse
from app.api.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException, ConflictException, BadRequestException
from app.utils.pagination import PaginationParams
from app.utils.filtering import parse_filter_params
from app.utils.response_utils import paginated_response

router = APIRouter(tags=["Teams"])

@router.post(
    "/projects/{project_id}/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new team",
    description="Create a new team for a project."
)
def create_team(
    project_id: str = Path(..., description="The ID of the project"),
    team_data: TeamBase = Body(..., description="The team data"),
    service: TeamService = Depends(get_team_service)
):
    """Create a new team.
    
    Args:
        project_id: The ID of the project.
        team_data: The team data.
        service: The team service.
        
    Returns:
        The created team.
        
    Raises:
        NotFoundException: If the project is not found.
        ConflictException: If a team with the same name already exists for the project.
    """
    try:
        return service.create_team(project_id, team_data.name, team_data.members)
    except (NotFoundException, ConflictException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/teams/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a team by ID",
    description="Get a team by its ID."
)
def get_team(
    team_id: int = Path(..., description="The ID of the team"),
    service: TeamService = Depends(get_team_service)
):
    """Get a team by ID.
    
    Args:
        team_id: The ID of the team.
        service: The team service.
        
    Returns:
        The team.
        
    Raises:
        NotFoundException: If the team is not found.
    """
    try:
        return service.get_team(team_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/teams/{team_id}/with-tasks",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a team with its tasks",
    description="Get a team by its ID including its assigned tasks."
)
def get_team_with_tasks(
    team_id: int = Path(..., description="The ID of the team"),
    service: TeamService = Depends(get_team_service)
):
    """Get a team with its tasks.
    
    Args:
        team_id: The ID of the team.
        service: The team service.
        
    Returns:
        The team with tasks.
        
    Raises:
        NotFoundException: If the team is not found.
    """
    try:
        return service.get_team_with_tasks(team_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/teams",
    response_model=PaginatedResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all teams for a project",
    description="Get all teams for a project with pagination, filtering, and search support."
)
def get_teams_for_project(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    search: Optional[str] = Depends(get_search_params),
    filter_params: Dict[str, Any] = Depends(get_filter_params),
    service: TeamService = Depends(get_team_service)
):
    """Get all teams for a project with pagination, filtering, and search.
    
    Args:
        request: The FastAPI request object.
        project_id: The ID of the project.
        pagination: Pagination parameters.
        search: Search term.
        filter_params: Filter parameters.
        service: The team service.
        
    Returns:
        Paginated list of teams for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        # Parse filter conditions
        filters = parse_filter_params(filter_params) if filter_params else None
        
        # Get paginated teams
        result = service.get_teams_for_project(project_id, pagination, filters, search)
        
        # Return paginated response
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="Teams retrieved successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.put(
    "/teams/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a team",
    description="Update a team."
)
def update_team(
    team_id: int = Path(..., description="The ID of the team"),
    team_data: TeamUpdate = Body(..., description="The team update data"),
    service: TeamService = Depends(get_team_service)
):
    """Update a team.
    
    Args:
        team_id: The ID of the team.
        team_data: The team update data.
        service: The team service.
        
    Returns:
        The updated team.
        
    Raises:
        NotFoundException: If the team is not found.
        ConflictException: If a team with the same name already exists for the project.
        BadRequestException: If no update fields are provided.
    """
    try:
        return service.update_team(team_id, team_data.name, team_data.members)
    except (NotFoundException, ConflictException, BadRequestException) as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete(
    "/teams/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete a team",
    description="Delete a team."
)
def delete_team(
    team_id: int = Path(..., description="The ID of the team"),
    service: TeamService = Depends(get_team_service)
):
    """Delete a team.
    
    Args:
        team_id: The ID of the team.
        service: The team service.
        
    Returns:
        The deleted team.
        
    Raises:
        NotFoundException: If the team is not found.
    """
    try:
        return service.delete_team(team_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/teams/search",
    response_model=PaginatedResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Search teams",
    description="Search teams by name or members for a project with pagination support."
)
def search_teams(
    project_id: str = Path(..., description="The ID of the project"),
    query: str = Query(..., description="The search query"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    service: TeamService = Depends(get_team_service)
):
    """Search teams with pagination support.
    
    Args:
        project_id: The ID of the project.
        query: The search query.
        pagination: Pagination parameters.
        service: The team service.
        
    Returns:
        Paginated list of teams matching the search query.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        result = service.search_teams(project_id, query, pagination)
        
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="Teams search completed successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/teams/count",
    response_model=int,
    status_code=status.HTTP_200_OK,
    summary="Count teams for a project",
    description="Count the number of teams for a project."
)
def count_teams_for_project(
    project_id: str = Path(..., description="The ID of the project"),
    service: TeamService = Depends(get_team_service)
):
    """Count teams for a project.
    
    Args:
        project_id: The ID of the project.
        service: The team service.
        
    Returns:
        The number of teams for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.count_teams_for_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)