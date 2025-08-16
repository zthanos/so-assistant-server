"""Project API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.projects import ProjectService
from app.repositories.projects import ProjectRepository
from app.api.schemas.projects import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectOutlineResponse
)
from app.core.exceptions import NotFoundException, BadRequestException


router = APIRouter()


def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository(db)


def get_project_service(
    repository: ProjectRepository = Depends(get_project_repository)
) -> ProjectService:
    """Get project service dependency."""
    return ProjectService(repository)


@router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project with the provided data."
)
def create_project(
    project_data: ProjectCreate = Body(..., description="The project data"),
    service: ProjectService = Depends(get_project_service)
):
    """Create a new project.
    
    Args:
        project_data: The project data.
        service: The project service.
        
    Returns:
        The created project.
        
    Raises:
        BadRequestException: If the project data is invalid.
    """
    try:
        return service.create_project(project_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects",
    response_model=List[ProjectResponse],
    status_code=status.HTTP_200_OK,
    summary="List all projects",
    description="Get a list of all projects with optional pagination."
)
def list_projects(
    skip: int = Query(0, description="The number of records to skip"),
    limit: int = Query(100, description="The maximum number of records to return"),
    service: ProjectService = Depends(get_project_service)
):
    """List all projects.
    
    Args:
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        service: The project service.
        
    Returns:
        A list of projects.
    """
    return service.list_projects(skip=skip, limit=limit)


@router.get(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a project by ID",
    description="Get a specific project by its ID."
)
def get_project(
    project_id: str = Path(..., description="The ID of the project"),
    service: ProjectService = Depends(get_project_service)
):
    """Get a project by ID.
    
    Args:
        project_id: The ID of the project.
        service: The project service.
        
    Returns:
        The project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.get_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/projects/{project_id}/outline",
    response_model=ProjectOutlineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project outline",
    description="Get a project with all its related entities (requirements, diagrams, teams, tasks)."
)
def get_project_outline(
    project_id: str = Path(..., description="The ID of the project"),
    service: ProjectService = Depends(get_project_service)
):
    """Get project outline with all related entities.
    
    Args:
        project_id: The ID of the project.
        service: The project service.
        
    Returns:
        The project outline with all related entities.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        project = service.get_project(project_id)
        return ProjectOutlineResponse.from_orm_with_latest(project=project)
        return service.get_project_outline(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/projects/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a project",
    description="Update an existing project with the provided data."
)
def update_project(
    project_id: str = Path(..., description="The ID of the project"),
    project_data: ProjectUpdate = Body(..., description="The project update data"),
    service: ProjectService = Depends(get_project_service)
):
    """Update a project.
    
    Args:
        project_id: The ID of the project.
        project_data: The project update data.
        service: The project service.
        
    Returns:
        The updated project.
        
    Raises:
        NotFoundException: If the project is not found.
        BadRequestException: If the project data is invalid.
    """
    try:
        return service.update_project(project_id, project_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    description="Delete an existing project and all its related entities."
)
def delete_project(
    project_id: str = Path(..., description="The ID of the project"),
    service: ProjectService = Depends(get_project_service)
):
    """Delete a project.
    
    Args:
        project_id: The ID of the project.
        service: The project service.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        service.delete_project(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))