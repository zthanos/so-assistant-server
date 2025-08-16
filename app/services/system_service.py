"""System service implementation."""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.system_repository import SystemRepository
from app.repositories.project_repository import ProjectRepository
from app.domain.models.systems import System, SystemType
from app.api.schemas.systems import (
    SystemCreate, SystemUpdate, SystemUpsert, SystemResponse, 
    SystemSearchFilters, SystemDependencyValidationResponse
)
from app.core.exceptions import NotFoundException, BadRequestException, DatabaseException
from app.exceptions.systems_teams_exceptions import (
    SystemNotFoundException, DuplicateSystemException, InvalidDependencyException,
    CircularDependencyException, SystemValidationException, SystemOperationException,
    SystemDependencyException
)

logger = logging.getLogger(__name__)


class SystemService:
    """Service for system operations with business logic."""
    
    def __init__(
        self, 
        repository: SystemRepository,
        project_repository: ProjectRepository
    ):
        """Initialize the service with repositories.
        
        Args:
            repository: The system repository.
            project_repository: The project repository for validation.
        """
        self.repository = repository
        self.project_repository = project_repository
    
    def create_system(self, db: Session, system_data: SystemCreate) -> SystemResponse:
        """Create a new system with project validation.
        
        Args:
            db: Database session.
            system_data: The system creation data.
            
        Returns:
            The created system response.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If the system data is invalid or name already exists.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Creating system for project {system_data.project_id}: {system_data.name}")
        
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, system_data.project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {system_data.project_id} not found",
                    resource_type="Project",
                    resource_id=system_data.project_id
                )
            
            # Check if system name already exists in the project
            existing_system = self.repository.get_by_project_and_name(
                db, system_data.project_id, system_data.name
            )
            if existing_system:
                raise DuplicateSystemException(
                    f"System with name '{system_data.name}' already exists in project {system_data.project_id}",
                    system_name=system_data.name,
                    project_id=system_data.project_id
                )
            
            # Validate dependencies if provided
            if system_data.dependencies:
                validation_result = self.repository.validate_dependencies(
                    db, system_data.project_id, system_data.dependencies
                )
                if not validation_result["valid"]:
                    error_msg = f"Invalid dependencies: {', '.join(validation_result['invalid_dependencies'])}"
                    raise BadRequestException(error_msg)
                
                # Check for circular dependencies
                circular_deps = self.repository.detect_circular_dependencies(
                    db, system_data.project_id, system_data.name, system_data.dependencies
                )
                if circular_deps:
                    error_msg = f"Circular dependencies detected: {', '.join(circular_deps)}"
                    raise BadRequestException(error_msg)
            
            # Create the system
            system = self.repository.create(db, obj_in=system_data)
            
            logger.info(f"Successfully created system {system.name} with ID {system.id}")
            return self._to_response(system)
            
        except (NotFoundException, DuplicateSystemException, InvalidDependencyException, CircularDependencyException):
            raise
        except Exception as e:
            logger.error(f"Error creating system {system_data.name}: {e}")
            raise SystemOperationException(
                f"Error creating system: {str(e)}", 
                operation="create",
                system_name=system_data.name,
                project_id=system_data.project_id,
                status_code=500
            )
    
    def get_system(self, db: Session, system_id: int) -> SystemResponse:
        """Get a system by ID.
        
        Args:
            db: Database session.
            system_id: The system ID.
            
        Returns:
            The system response.
            
        Raises:
            NotFoundException: If the system doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            system = self.repository.get_or_404(db, system_id)
            return self._to_response(system)
            
        except NotFoundException:
            raise SystemNotFoundException(
                f"System with ID {system_id} not found",
                system_id=system_id
            )
        except Exception as e:
            logger.error(f"Error retrieving system {system_id}: {e}")
            raise SystemOperationException(
                f"Error retrieving system: {str(e)}", 
                operation="get",
                status_code=500
            )
    
    def upsert_system(self, db: Session, system_data: SystemUpsert) -> SystemResponse:
        """Create or update a system using project_id + name as natural key.
        
        Args:
            db: Database session.
            system_data: The system upsert data.
            
        Returns:
            The created or updated system response.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If the system data is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Upserting system for project {system_data.project_id}: {system_data.name}")
        
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, system_data.project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {system_data.project_id} not found",
                    resource_type="Project",
                    resource_id=system_data.project_id
                )
            
            # Validate dependencies if provided
            if system_data.dependencies:
                validation_result = self.repository.validate_dependencies(
                    db, system_data.project_id, system_data.dependencies
                )
                if not validation_result["valid"]:
                    error_msg = f"Invalid dependencies: {', '.join(validation_result['invalid_dependencies'])}"
                    raise BadRequestException(error_msg)
                
                # Check for circular dependencies
                circular_deps = self.repository.detect_circular_dependencies(
                    db, system_data.project_id, system_data.name, system_data.dependencies
                )
                if circular_deps:
                    error_msg = f"Circular dependencies detected: {', '.join(circular_deps)}"
                    raise BadRequestException(error_msg)
            
            # Perform upsert
            system_dict = system_data.dict(exclude={'project_id'})
            system = self.repository.upsert_system(
                db, system_data.project_id, system_data.name, system_dict
            )
            
            logger.info(f"Successfully upserted system {system.name} with ID {system.id}")
            return self._to_response(system)
            
        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error upserting system {system_data.name}: {e}")
            raise DatabaseException(f"Error upserting system: {str(e)}", original_exception=e)
    
    def update_system(self, db: Session, system_id: int, system_data: SystemUpdate) -> SystemResponse:
        """Update an existing system.
        
        Args:
            db: Database session.
            system_id: The system ID.
            system_data: The system update data.
            
        Returns:
            The updated system response.
            
        Raises:
            NotFoundException: If the system doesn't exist.
            BadRequestException: If the update data is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Updating system {system_id}")
        
        try:
            # Get the existing system
            existing_system = self.repository.get_or_404(db, system_id)
            
            # If name is being updated, check for duplicates
            if system_data.name and system_data.name != existing_system.name:
                duplicate_system = self.repository.get_by_project_and_name(
                    db, existing_system.project_id, system_data.name
                )
                if duplicate_system:
                    raise BadRequestException(
                        f"System with name '{system_data.name}' already exists in project {existing_system.project_id}"
                    )
            
            # Validate dependencies if provided
            if system_data.dependencies is not None:
                validation_result = self.repository.validate_dependencies(
                    db, existing_system.project_id, system_data.dependencies
                )
                if not validation_result["valid"]:
                    error_msg = f"Invalid dependencies: {', '.join(validation_result['invalid_dependencies'])}"
                    raise BadRequestException(error_msg)
                
                # Check for circular dependencies
                system_name = system_data.name if system_data.name else existing_system.name
                circular_deps = self.repository.detect_circular_dependencies(
                    db, existing_system.project_id, system_name, system_data.dependencies
                )
                if circular_deps:
                    error_msg = f"Circular dependencies detected: {', '.join(circular_deps)}"
                    raise BadRequestException(error_msg)
            
            # Update the system
            system = self.repository.update_by_id(db, id=system_id, obj_in=system_data)
            
            logger.info(f"Successfully updated system {system.name} with ID {system.id}")
            return self._to_response(system)
            
        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(f"Error updating system {system_id}: {e}")
            raise DatabaseException(f"Error updating system: {str(e)}", original_exception=e)
    
    def delete_system(self, db: Session, system_id: int) -> bool:
        """Delete a system.
        
        Args:
            db: Database session.
            system_id: The system ID.
            
        Returns:
            True if the system was deleted.
            
        Raises:
            NotFoundException: If the system doesn't exist.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Deleting system {system_id}")
        
        try:
            # Check if system exists and get its details for logging
            system = self.repository.get_or_404(db, system_id)
            system_name = system.name
            
            # Delete the system
            self.repository.delete(db, id=system_id)
            
            logger.info(f"Successfully deleted system {system_name} with ID {system_id}")
            return True
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error deleting system {system_id}: {e}")
            raise DatabaseException(f"Error deleting system: {str(e)}", original_exception=e)
    
    def list_systems(
        self, 
        db: Session, 
        project_id: str, 
        filters: Optional[SystemSearchFilters] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[SystemResponse]:
        """List systems for a project with optional filtering.
        
        Args:
            db: Database session.
            project_id: The project ID.
            filters: Optional search filters.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of system responses.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Get systems based on filters
            if filters:
                systems = self.repository.search_systems(db, project_id, filters, skip, limit)
            else:
                systems = self.repository.get_by_project(db, project_id, skip, limit)
            
            return [self._to_response(system) for system in systems]
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error listing systems for project {project_id}: {e}")
            raise DatabaseException(f"Error listing systems: {str(e)}", original_exception=e)
    
    def validate_system_dependencies(
        self, 
        db: Session, 
        project_id: str, 
        dependencies: List[str]
    ) -> SystemDependencyValidationResponse:
        """Validate system dependencies.
        
        Args:
            db: Database session.
            project_id: The project ID.
            dependencies: List of dependency names to validate.
            
        Returns:
            Dependency validation response.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            # Validate dependencies
            validation_result = self.repository.validate_dependencies(db, project_id, dependencies)
            
            return SystemDependencyValidationResponse(
                valid=validation_result["valid"],
                invalid_dependencies=validation_result["invalid_dependencies"],
                circular_dependencies=validation_result["circular_dependencies"]
            )
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error validating dependencies for project {project_id}: {e}")
            raise DatabaseException(f"Error validating dependencies: {str(e)}", original_exception=e)
    
    def get_systems_by_type(
        self, 
        db: Session, 
        project_id: str, 
        system_type: SystemType,
        skip: int = 0,
        limit: int = 100
    ) -> List[SystemResponse]:
        """Get systems by project and type.
        
        Args:
            db: Database session.
            project_id: The project ID.
            system_type: The system type to filter by.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of system responses.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            systems = self.repository.get_systems_by_type(db, project_id, system_type, skip, limit)
            return [self._to_response(system) for system in systems]
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting {system_type.value} systems for project {project_id}: {e}")
            raise DatabaseException(f"Error getting systems by type: {str(e)}", original_exception=e)
    
    def get_systems_with_dependencies(
        self, 
        db: Session, 
        project_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[SystemResponse]:
        """Get systems that have dependencies.
        
        Args:
            db: Database session.
            project_id: The project ID.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.
            
        Returns:
            List of system responses.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            systems = self.repository.get_systems_with_dependencies(db, project_id, skip, limit)
            return [self._to_response(system) for system in systems]
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting systems with dependencies for project {project_id}: {e}")
            raise DatabaseException(f"Error getting systems with dependencies: {str(e)}", original_exception=e)
    
    def count_systems(
        self, 
        db: Session, 
        project_id: str, 
        filters: Optional[SystemSearchFilters] = None
    ) -> int:
        """Count systems for a project with optional filtering.
        
        Args:
            db: Database session.
            project_id: The project ID.
            filters: Optional search filters.
            
        Returns:
            Number of systems matching the criteria.
            
        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id
                )
            
            return self.repository.count_by_project(db, project_id, filters)
            
        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error counting systems for project {project_id}: {e}")
            raise DatabaseException(f"Error counting systems: {str(e)}", original_exception=e)
    
    def _to_response(self, system: System) -> SystemResponse:
        """Convert a System model to SystemResponse.
        
        Args:
            system: The system model.
            
        Returns:
            The system response.
        """
        return SystemResponse(
            id=system.id,
            project_id=system.project_id,
            name=system.name,
            description=system.description,
            type=system.type,
            dependencies=system.dependencies or [],
            created_at=system.created_at,
            updated_at=system.updated_at
        )