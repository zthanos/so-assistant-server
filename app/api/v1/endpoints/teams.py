"""Team API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.team_service import TeamService
from app.repositories.team_repository import TeamRepository
from app.repositories.project_repository import ProjectRepository
from app.api.schemas.teams import (
    TeamUpdate,
    TeamUpsert,
    TeamResponse,
    TeamSearchFilters
)
from app.api.schemas.common import PaginatedResponse, create_paginated_response
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException
from app.exceptions.systems_teams_exceptions import (
    TeamNotFoundException, DuplicateTeamException, TeamValidationException,
    TeamMemberValidationException, TeamOperationException
)

router = APIRouter(prefix="/projects/{project_id}/teams", tags=["Teams"])


def get_team_repository() -> TeamRepository:
    """Get team repository dependency."""
    return TeamRepository()


def get_project_repository() -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository()


def get_team_service(
    team_repository: TeamRepository = Depends(get_team_repository),
    project_repository: ProjectRepository = Depends(get_project_repository)
) -> TeamService:
    """Get team service dependency."""
    return TeamService(team_repository, project_repository)


@router.post(
    "",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert a team",
    description="Create or update a team using project_id and name as natural key."
)
def upsert_team(
    project_id: str = Path(..., description="The project ID"),
    team_data: TeamUpsert = Body(..., description="The team upsert data"),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Create or update a team using project_id and name as natural key.
    
    Args:
        project_id: The project ID from the URL path.
        team_data: The team upsert data.
        db: Database session.
        service: The team service.
        
    Returns:
        The created or updated team.
        
    Raises:
        HTTPException: If the project doesn't exist or data is invalid.
    """
    try:
        # Override project_id from path parameter
        team_data.project_id = project_id
        return service.upsert_team(db, team_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a team by ID",
    description="Retrieve a specific team by its ID."
)
def get_team(
    project_id: str = Path(..., description="The project ID"),
    team_id: int = Path(..., description="The team ID", gt=0),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Get a team by ID.
    
    Args:
        project_id: The project ID from the URL path.
        team_id: The team ID.
        db: Database session.
        service: The team service.
        
    Returns:
        The team data.
        
    Raises:
        HTTPException: If the team doesn't exist.
    """
    try:
        return service.get_team(db, team_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "",
    response_model=PaginatedResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="List teams",
    description="List teams for a project with optional filtering and pagination."
)
def list_teams(
    project_id: str = Path(..., description="The project ID"),
    name: Optional[str] = Query(None, description="Filter by team name (partial match)"),
    role: Optional[str] = Query(None, description="Filter by team role (partial match)"),
    member: Optional[str] = Query(None, description="Filter by team member name (partial match)"),
    responsibility: Optional[str] = Query(None, description="Filter by responsibility (partial match)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """List teams for a project with optional filtering and pagination.
    
    Args:
        project_id: The project ID from the URL path.
        name: Optional name filter (partial match).
        role: Optional role filter (partial match).
        member: Optional member filter (partial match).
        responsibility: Optional responsibility filter (partial match).
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Database session.
        service: The team service.
        
    Returns:
        Paginated list of teams.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        # Create filters object
        filters = TeamSearchFilters(
            name=name,
            role=role,
            member=member,
            responsibility=responsibility
        )
        
        # Get teams and total count
        teams = service.list_teams(db, project_id, filters, skip, limit)
        total_count = service.count_teams(db, project_id, filters)
        
        return create_paginated_response(
            items=teams,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a team",
    description="Update an existing team with the provided data."
)
def update_team(
    project_id: str = Path(..., description="The project ID"),
    team_id: int = Path(..., description="The team ID", gt=0),
    team_data: TeamUpdate = Body(..., description="The team update data"),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Update an existing team.
    
    Args:
        project_id: The project ID from the URL path.
        team_id: The team ID.
        team_data: The team update data.
        db: Database session.
        service: The team service.
        
    Returns:
        The updated team.
        
    Raises:
        HTTPException: If the team doesn't exist or data is invalid.
    """
    try:
        return service.update_team(db, team_id, team_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a team",
    description="Delete an existing team."
)
def delete_team(
    project_id: str = Path(..., description="The project ID"),
    team_id: int = Path(..., description="The team ID", gt=0),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Delete an existing team.
    
    Args:
        project_id: The project ID from the URL path.
        team_id: The team ID.
        db: Database session.
        service: The team service.
        
    Raises:
        HTTPException: If the team doesn't exist.
    """
    try:
        service.delete_team(db, team_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/by-role/{role}",
    response_model=PaginatedResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Get teams by role",
    description="Get teams filtered by role for a project."
)
def get_teams_by_role(
    project_id: str = Path(..., description="The project ID"),
    role: str = Path(..., description="The team role to filter by"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Get teams by role for a project.
    
    Args:
        project_id: The project ID from the URL path.
        role: The team role to filter by.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Database session.
        service: The team service.
        
    Returns:
        Paginated list of teams with the specified role.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        teams = service.get_teams_by_role(db, project_id, role, skip, limit)
        
        # For role-specific queries, we need to count separately
        filters = TeamSearchFilters(role=role)
        total_count = service.count_teams(db, project_id, filters)
        
        return create_paginated_response(
            items=teams,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/with-member/{member_name}",
    response_model=PaginatedResponse[TeamResponse],
    status_code=status.HTTP_200_OK,
    summary="Get teams with specific member",
    description="Get teams that have a specific member for a project."
)
def get_teams_with_member(
    project_id: str = Path(..., description="The project ID"),
    member_name: str = Path(..., description="The member name to search for"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Get teams that have a specific member for a project.
    
    Args:
        project_id: The project ID from the URL path.
        member_name: The member name to search for.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Database session.
        service: The team service.
        
    Returns:
        Paginated list of teams containing the specified member.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        teams = service.get_teams_with_member(db, project_id, member_name, skip, limit)
        
        # For member-specific queries, we need to count separately
        filters = TeamSearchFilters(member=member_name)
        total_count = service.count_teams(db, project_id, filters)
        
        return create_paginated_response(
            items=teams,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/validate-members",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Validate team members",
    description="Validate team member names for duplicates and empty values."
)
def validate_team_members(
    project_id: str = Path(..., description="The project ID"),
    members: List[str] = Body(..., description="List of member names to validate"),
    service: TeamService = Depends(get_team_service)
):
    """Validate team member names.
    
    Args:
        project_id: The project ID from the URL path.
        members: List of member names to validate.
        service: The team service.
        
    Returns:
        Member validation results.
        
    Raises:
        HTTPException: If there's an error during validation.
    """
    try:
        return service.validate_team_members(members)
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/analyze-responsibilities",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Analyze team responsibilities",
    description="Analyze team responsibilities for overlaps and gaps in a project."
)
def analyze_team_responsibilities(
    project_id: str = Path(..., description="The project ID"),
    db: Session = Depends(get_db),
    service: TeamService = Depends(get_team_service)
):
    """Analyze team responsibilities for overlaps and gaps.
    
    Args:
        project_id: The project ID from the URL path.
        db: Database session.
        service: The team service.
        
    Returns:
        Responsibility analysis results.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        return service.analyze_team_responsibilities(db, project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")