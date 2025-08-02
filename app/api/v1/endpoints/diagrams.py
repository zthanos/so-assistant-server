"""Diagram API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.diagrams import DiagramService
from app.repositories.diagrams import DiagramRepository
from app.repositories.projects import ProjectRepository
from app.api.schemas.diagrams import (
    DiagramCreate,
    DiagramUpdate,
    DiagramResponse
)
from app.core.exceptions import NotFoundException, BadRequestException


router = APIRouter()


def get_diagram_repository(db: Session = Depends(get_db)) -> DiagramRepository:
    """Get diagram repository dependency."""
    return DiagramRepository(db)


def get_project_repository(db: Session = Depends(get_db)) -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository(db)


def get_diagram_service(
    diagram_repository: DiagramRepository = Depends(get_diagram_repository),
    project_repository: ProjectRepository = Depends(get_project_repository)
) -> DiagramService:
    """Get diagram service dependency."""
    return DiagramService(diagram_repository, project_repository)


@router.post(
    "/projects/{project_id}/diagrams",
    response_model=DiagramResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new diagram",
    description="Create a new diagram for a project."
)
def create_diagram(
    project_id: str = Path(..., description="The ID of the project"),
    diagram_data: DiagramCreate = Body(..., description="The diagram data"),
    service: DiagramService = Depends(get_diagram_service)
):
    """Create a new diagram for a project.
    
    Args:
        project_id: The ID of the project.
        diagram_data: The diagram data.
        service: The diagram service.
        
    Returns:
        The created diagram.
        
    Raises:
        NotFoundException: If the project is not found.
        BadRequestException: If the diagram data is invalid.
    """
    try:
        return service.create_diagram(project_id, diagram_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/projects/{project_id}/diagrams",
    response_model=List[DiagramResponse],
    status_code=status.HTTP_200_OK,
    summary="List diagrams for a project",
    description="Get all diagrams for a specific project."
)
def list_diagrams(
    project_id: str = Path(..., description="The ID of the project"),
    skip: int = Query(0, description="The number of records to skip"),
    limit: int = Query(100, description="The maximum number of records to return"),
    service: DiagramService = Depends(get_diagram_service)
):
    """List diagrams for a project.
    
    Args:
        project_id: The ID of the project.
        skip: The number of records to skip.
        limit: The maximum number of records to return.
        service: The diagram service.
        
    Returns:
        A list of diagrams for the project.
        
    Raises:
        NotFoundException: If the project is not found.
    """
    try:
        return service.list_diagrams(project_id, skip=skip, limit=limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/projects/{project_id}/diagrams/{diagram_id}",
    response_model=DiagramResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a diagram by ID",
    description="Get a specific diagram by its ID within a project."
)
def get_diagram(
    project_id: str = Path(..., description="The ID of the project"),
    diagram_id: int = Path(..., description="The ID of the diagram"),
    service: DiagramService = Depends(get_diagram_service)
):
    """Get a diagram by ID.
    
    Args:
        project_id: The ID of the project.
        diagram_id: The ID of the diagram.
        service: The diagram service.
        
    Returns:
        The diagram.
        
    Raises:
        NotFoundException: If the project or diagram is not found.
    """
    try:
        return service.get_diagram(project_id, diagram_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put(
    "/projects/{project_id}/diagrams/{diagram_id}",
    response_model=DiagramResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a diagram",
    description="Update an existing diagram with the provided data."
)
def update_diagram(
    project_id: str = Path(..., description="The ID of the project"),
    diagram_id: int = Path(..., description="The ID of the diagram"),
    diagram_data: DiagramUpdate = Body(..., description="The diagram update data"),
    service: DiagramService = Depends(get_diagram_service)
):
    """Update a diagram.
    
    Args:
        project_id: The ID of the project.
        diagram_id: The ID of the diagram.
        diagram_data: The diagram update data.
        service: The diagram service.
        
    Returns:
        The updated diagram.
        
    Raises:
        NotFoundException: If the project or diagram is not found.
        BadRequestException: If the diagram data is invalid.
    """
    try:
        return service.update_diagram(project_id, diagram_id, diagram_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/projects/{project_id}/diagrams/{diagram_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a diagram",
    description="Delete an existing diagram from a project."
)
def delete_diagram(
    project_id: str = Path(..., description="The ID of the project"),
    diagram_id: int = Path(..., description="The ID of the diagram"),
    service: DiagramService = Depends(get_diagram_service)
):
    """Delete a diagram.
    
    Args:
        project_id: The ID of the project.
        diagram_id: The ID of the diagram.
        service: The diagram service.
        
    Raises:
        NotFoundException: If the project or diagram is not found.
    """
    try:
        service.delete_diagram(project_id, diagram_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))