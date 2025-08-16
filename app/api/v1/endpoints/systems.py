"""System API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.system_service import SystemService
from app.repositories.system_repository import SystemRepository
from app.repositories.project_repository import ProjectRepository
from app.api.schemas.systems import (
    SystemUpdate,
    SystemUpsert,
    SystemResponse,
    SystemType,
    SystemSearchFilters,
    SystemDependencyValidation,
    SystemDependencyValidationResponse
)
from app.api.schemas.common import PaginatedResponse, create_paginated_response
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException
from app.exceptions.systems_teams_exceptions import (
    SystemNotFoundException, DuplicateSystemException, InvalidDependencyException,
    CircularDependencyException, SystemValidationException, SystemOperationException
)

router = APIRouter(prefix="/projects/{project_id}/systems", tags=["Systems"])


def get_system_repository() -> SystemRepository:
    """Get system repository dependency."""
    return SystemRepository()


def get_project_repository() -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository()


def get_system_service(
    system_repository: SystemRepository = Depends(get_system_repository),
    project_repository: ProjectRepository = Depends(get_project_repository)
) -> SystemService:
    """Get system service dependency."""
    return SystemService(system_repository, project_repository)


@router.post(
    "",
    response_model=SystemResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert a system",
    description="Create or update a system using project_id and name as natural key."
)
def upsert_system(
    project_id: str = Path(..., description="The project ID"),
    system_data: SystemUpsert = Body(..., description="The system upsert data"),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Create or update a system using project_id and name as natural key.
    
    Args:
        project_id: The project ID from the URL path.
        system_data: The system upsert data.
        db: Database session.
        service: The system service.
        
    Returns:
        The created or updated system.
        
    Raises:
        HTTPException: If the project doesn't exist or data is invalid.
    """
    try:
        # Override project_id from path parameter
        system_data.project_id = project_id
        return service.upsert_system(db, system_data)
    except (NotFoundException, SystemNotFoundException) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except (DuplicateSystemException, InvalidDependencyException, CircularDependencyException, SystemValidationException) as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except (BadRequestException, SystemOperationException) as e:
        raise HTTPException(status_code=e.status_code if hasattr(e, 'status_code') else 400, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/{system_id}",
    response_model=SystemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a system by ID",
    description="Retrieve a specific system by its ID."
)
def get_system(
    system_id: int = Path(..., description="The system ID", gt=0),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Get a system by ID.
    
    Args:
        system_id: The system ID.
        db: Database session.
        service: The system service.
        
    Returns:
        The system data.
        
    Raises:
        HTTPException: If the system doesn't exist.
    """
    try:
        return service.get_system(db, system_id)
    except (NotFoundException, SystemNotFoundException) as e:
        raise HTTPException(status_code=404, detail=str(e))
    except SystemOperationException as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "",
    response_model=PaginatedResponse[SystemResponse],
    status_code=status.HTTP_200_OK,
    summary="List systems",
    description="List systems for a project with optional filtering and pagination."
)
def list_systems(
    project_id: str = Path(..., description="The project ID"),
    name: Optional[str] = Query(None, description="Filter by system name (partial match)"),
    type: Optional[SystemType] = Query(None, description="Filter by system type"),
    description: Optional[str] = Query(None, description="Filter by description (partial match)"),
    has_dependencies: Optional[bool] = Query(None, description="Filter systems with/without dependencies"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """List systems for a project with optional filtering and pagination.
    
    Args:
        project_id: The project ID from the URL path.
        name: Optional name filter (partial match).
        type: Optional system type filter.
        description: Optional description filter (partial match).
        has_dependencies: Optional filter for systems with/without dependencies.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Database session.
        service: The system service.
        
    Returns:
        Paginated list of systems.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        # Create filters object
        filters = SystemSearchFilters(
            name=name,
            type=type,
            description=description,
            has_dependencies=has_dependencies
        )
        
        # Get systems and total count
        systems = service.list_systems(db, project_id, filters, skip, limit)
        total_count = service.count_systems(db, project_id, filters)
        
        return create_paginated_response(
            items=systems,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch(
    "/{system_id}",
    response_model=SystemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a system",
    description="Update an existing system with the provided data."
)
def update_system(
    system_id: int = Path(..., description="The system ID", gt=0),
    system_data: SystemUpdate = Body(..., description="The system update data"),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Update an existing system.
    
    Args:
        system_id: The system ID.
        system_data: The system update data.
        db: Database session.
        service: The system service.
        
    Returns:
        The updated system.
        
    Raises:
        HTTPException: If the system doesn't exist or data is invalid.
    """
    try:
        return service.update_system(db, system_id, system_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete(
    "/{system_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a system",
    description="Delete an existing system."
)
def delete_system(
    system_id: int = Path(..., description="The system ID", gt=0),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Delete an existing system.
    
    Args:
        system_id: The system ID.
        db: Database session.
        service: The system service.
        
    Raises:
        HTTPException: If the system doesn't exist.
    """
    try:
        service.delete_system(db, system_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/by-type/{system_type}",
    response_model=PaginatedResponse[SystemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get systems by type",
    description="Get systems filtered by type for a project."
)
def get_systems_by_type(
    project_id: str = Path(..., description="The project ID"),
    system_type: SystemType = Path(..., description="The system type"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Get systems by type for a project.
    
    Args:
        project_id: The project ID from the URL path.
        system_type: The system type to filter by.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Database session.
        service: The system service.
        
    Returns:
        Paginated list of systems of the specified type.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        systems = service.get_systems_by_type(db, project_id, system_type, skip, limit)
        
        # For type-specific queries, we need to count separately
        filters = SystemSearchFilters(type=system_type)
        total_count = service.count_systems(db, project_id, filters)
        
        return create_paginated_response(
            items=systems,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/with-dependencies",
    response_model=PaginatedResponse[SystemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get systems with dependencies",
    description="Get systems that have dependencies for a project."
)
def get_systems_with_dependencies(
    project_id: str = Path(..., description="The project ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Get systems that have dependencies for a project.
    
    Args:
        project_id: The project ID from the URL path.
        skip: Number of records to skip for pagination.
        limit: Maximum number of records to return.
        db: Database session.
        service: The system service.
        
    Returns:
        Paginated list of systems with dependencies.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        systems = service.get_systems_with_dependencies(db, project_id, skip, limit)
        
        # For dependency-specific queries, we need to count separately
        filters = SystemSearchFilters(has_dependencies=True)
        total_count = service.count_systems(db, project_id, filters)
        
        return create_paginated_response(
            items=systems,
            total=total_count,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post(
    "/validate-dependencies",
    response_model=SystemDependencyValidationResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate system dependencies",
    description="Validate that system dependencies exist and check for circular dependencies."
)
def validate_system_dependencies(
    project_id: str = Path(..., description="The project ID"),
    validation_data: SystemDependencyValidation = Body(..., description="The dependency validation data"),
    db: Session = Depends(get_db),
    service: SystemService = Depends(get_system_service)
):
    """Validate system dependencies.
    
    Args:
        project_id: The project ID from the URL path.
        validation_data: The dependency validation data.
        db: Database session.
        service: The system service.
        
    Returns:
        Dependency validation results.
        
    Raises:
        HTTPException: If the project doesn't exist.
    """
    try:
        # Override project_id from path parameter
        return service.validate_system_dependencies(
            db, project_id, validation_data.dependencies
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DatabaseException as e:
        raise HTTPException(status_code=500, detail="Internal server error")