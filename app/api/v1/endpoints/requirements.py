"""Requirement API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.requirements import RequirementService
from app.repositories.requirements import RequirementRepository
from app.repositories.projects import ProjectRepository
from app.api.schemas.requirements import (
    RequirementCreate,
    RequirementUpdate,
    RequirementResponse
)
from app.core.exceptions import NotFoundException, BadRequestException


router = APIRouter()


def get_requirement_repository(db: Session = Depends(get_db)) -> RequirementRepository:
    """Get requirement repository dependency."""
    return RequirementRepository(db)


def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository(db)


def get_requirement_service(
    requirement_repository: RequirementRepository = Depends(get_requirement_repository),
    project_repository: ProjectRepository = Depends(get_project_repository)
) -> RequirementService:
    """Get requirement service dependency."""
    return RequirementService(requirement_repository, project_repository)


@router.post(
    "/projects/{project_id}/requirements",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new requirement",
    description="Create a new requirement for a project."
)
def create_requirement(
    project_id: str = Path(..., description="The ID of the project"),
    requirement_data: RequirementCreate = Body(..., description="The requirement data"),
    service: RequirementService = Depends(get_requirement_service)
):
    """Create a new requirement for a project.
    
    Args:
        project_id: The ID of the project.
        requirement_data: The requirement data.
        service: The requirement service.
        
    Returns:
        The created requirement.
        
    Raises:
        NotFoundException: If the project is not found.
        BadRequestException: If the requirement data is invalid.
    """
    try:
        return service.create_requirement(project_id, requirement_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects/{project_id}/requirements",
    response_model=List[RequirementResponse],
    status_code=status.HTTP_200_OK,
    summary="List requirements for a project",
    description="Get all requirements for a specific project."
)
def list_requirements(
    project_id: str = Path(..., description="The ID of the project"),
    skip: int = Query(0, description="The number of records to skip"),
    limit: int = Query(100, description="The maximum number of records to return"),
    service: RequirementService = Depends(get_requirement_service)
):
    """List requirements for a project.
    
    Args:
        project_id: The ID of the project.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        service: The requirement service.
        
    Returns:
        A list of requirements for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.list_requirements(project_id, skip=skip, limit=limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/projects/{project_id}/requirements/{requirement_id}",
    response_model=RequirementResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a requirement by ID",
    description="Get a specific requirement by its ID within a project."
)
def get_requirement(
    project_id: str = Path(..., description="The ID of the project"),
    requirement_id: int = Path(..., description="The ID of the requirement"),
    service: RequirementService = Depends(get_requirement_service)
):
    """Get a requirement by ID.
    
    Args:
        project_id: The ID of the project.
        requirement_id: The ID of the requirement.
        service: The requirement service.
        
    Returns:
        The requirement.
        
    Raises:
        NotFoundException: If the project or requirement is not found.
    """
    try:
        return service.get_requirement(project_id, requirement_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/projects/{project_id}/requirements/{requirement_id}",
    response_model=RequirementResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a requirement",
    description="Update an existing requirement with the provided data."
)
def update_requirement(
    project_id: str = Path(..., description="The ID of the project"),
    requirement_id: int = Path(..., description="The ID of the requirement"),
    requirement_data: RequirementUpdate = Body(..., description="The requirement update data"),
    service: RequirementService = Depends(get_requirement_service)
):
    """Update a requirement.
    
    Args:
        project_id: The ID of the project.
        requirement_id: The ID of the requirement.
        requirement_data: The requirement update data.
        service: The requirement service.
        
    Returns:
        The updated requirement.
        
    Raises:
        NotFoundException: If the project or requirement is not found.
        BadRequestException: If the requirement data is invalid.
    """
    try:
        return service.update_requirement(project_id, requirement_id, requirement_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/projects/{project_id}/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a requirement",
    description="Delete an existing requirement from a project."
)
def delete_requirement(
    project_id: str = Path(..., description="The ID of the project"),
    requirement_id: int = Path(..., description="The ID of the requirement"),
    service: RequirementService = Depends(get_requirement_service)
):
    """Delete a requirement.
    
    Args:
        project_id: The ID of the project.
        requirement_id: The ID of the requirement.
        service: The requirement service.
        
    Raises:
        NotFoundException: If the project or requirement is not found.
    """
    try:
        service.delete_requirement(project_id, requirement_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))