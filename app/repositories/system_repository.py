"""System repository implementation."""

import logging
import time
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text

from app.repositories.base import CRUDRepository
from app.domain.models.systems import System, SystemType
from app.api.schemas.systems import SystemCreate, SystemUpdate, SystemSearchFilters
from app.core.exceptions import (
    NotFoundException,
    DatabaseException,
    BadRequestException,
)

logger = logging.getLogger(__name__)


class SystemRepository(CRUDRepository[System, SystemCreate, SystemUpdate]):
    """Repository for systems with project-specific operations."""

    def __init__(self):
        """Initialize the repository with the System model."""
        super().__init__(System)

    def get_by_project(
        self, db: Session, project_id: str, skip: int = 0, limit: int = 100
    ) -> List[System]:
        """Get systems by project.

        Args:
            db: Database session.
            project_id: The ID of the project.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of systems.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        start_time = time.time()

        try:
            query = db.query(System).filter(System.project_id == project_id)
            systems = query.offset(skip).limit(limit).all()

            execution_time = int((time.time() - start_time) * 1000)
            logger.info(
                f"Retrieved {len(systems)} systems for project {project_id} in {execution_time}ms"
            )

            return systems

        except Exception as e:
            logger.error(f"Error retrieving systems for project {project_id}: {e}")
            raise DatabaseException(
                f"Error retrieving systems: {str(e)}", original_exception=e
            )

    def get_by_project_and_name(
        self, db: Session, project_id: str, name: str
    ) -> Optional[System]:
        """Get a system by project ID and name.

        Args:
            db: Database session.
            project_id: The ID of the project.
            name: The name of the system.

        Returns:
            The system if found, None otherwise.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            return (
                db.query(System)
                .filter(and_(System.project_id == project_id, System.name == name))
                .first()
            )

        except Exception as e:
            logger.error(
                f"Error retrieving system {name} for project {project_id}: {e}"
            )
            raise DatabaseException(
                f"Error retrieving system: {str(e)}", original_exception=e
            )

    def search_systems(
        self,
        db: Session,
        project_id: str,
        filters: SystemSearchFilters,
        skip: int = 0,
        limit: int = 100,
    ) -> List[System]:
        """Search systems with filters.

        Args:
            db: Database session.
            project_id: The ID of the project.
            filters: Search filters.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of filtered systems.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        start_time = time.time()

        try:
            query = db.query(System).filter(System.project_id == project_id)

            # Apply filters
            if filters.name:
                query = query.filter(System.name.ilike(f"%{filters.name}%"))

            if filters.type:
                query = query.filter(System.type == filters.type)

            if filters.description:
                query = query.filter(
                    System.description.ilike(f"%{filters.description}%")
                )

            if filters.has_dependencies is not None:
                if filters.has_dependencies:
                    # Systems with dependencies (non-empty JSON array)
                    query = query.filter(
                        and_(
                            System.dependencies.isnot(None),
                            func.json_array_length(System.dependencies) > 0,
                        )
                    )
                else:
                    # Systems without dependencies (empty or null JSON array)
                    query = query.filter(
                        or_(
                            System.dependencies.is_(None),
                            func.json_array_length(System.dependencies) == 0,
                        )
                    )

            # Order by name for consistent results
            query = query.order_by(System.name)

            systems = query.offset(skip).limit(limit).all()

            execution_time = int((time.time() - start_time) * 1000)
            logger.info(
                f"Search returned {len(systems)} systems for project {project_id} in {execution_time}ms"
            )

            return systems

        except Exception as e:
            logger.error(f"Error searching systems for project {project_id}: {e}")
            raise DatabaseException(
                f"Error searching systems: {str(e)}", original_exception=e
            )

    def count_by_project(
        self,
        db: Session,
        project_id: str,
        filters: Optional[SystemSearchFilters] = None,
    ) -> int:
        """Count systems by project with optional filters.

        Args:
            db: Database session.
            project_id: The ID of the project.
            filters: Optional search filters.

        Returns:
            Number of systems matching the criteria.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(func.count(System.id)).filter(
                System.project_id == project_id
            )

            if filters:
                if filters.name:
                    query = query.filter(System.name.ilike(f"%{filters.name}%"))

                if filters.type:
                    query = query.filter(System.type == filters.type)

                if filters.description:
                    query = query.filter(
                        System.description.ilike(f"%{filters.description}%")
                    )

                if filters.has_dependencies is not None:
                    if filters.has_dependencies:
                        query = query.filter(
                            and_(
                                System.dependencies.isnot(None),
                                func.json_array_length(System.dependencies) > 0,
                            )
                        )
                    else:
                        query = query.filter(
                            or_(
                                System.dependencies.is_(None),
                                func.json_array_length(System.dependencies) == 0,
                            )
                        )

            return query.scalar()

        except Exception as e:
            logger.error(f"Error counting systems for project {project_id}: {e}")
            raise DatabaseException(
                f"Error counting systems: {str(e)}", original_exception=e
            )

    def validate_dependencies(
        self, db: Session, project_id: str, dependencies: List[str]
    ) -> Dict[str, Any]:
        """Validate system dependencies.

        Args:
            db: Database session.
            project_id: The ID of the project.
            dependencies: List of dependency names to validate.

        Returns:
            Dictionary with validation results.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            if not dependencies:
                return {
                    "valid": True,
                    "invalid_dependencies": [],
                    "circular_dependencies": [],
                }

            # Get all existing system names in the project
            existing_systems = (
                db.query(System.name).filter(System.project_id == project_id).all()
            )
            existing_names = {system.name for system in existing_systems}

            # Find invalid dependencies (systems that don't exist)
            invalid_dependencies = [
                dep for dep in dependencies if dep not in existing_names
            ]

            # For now, we'll implement basic circular dependency detection
            # This can be enhanced later with more sophisticated graph analysis
            circular_dependencies = []

            return {
                "valid": len(invalid_dependencies) == 0,
                "invalid_dependencies": invalid_dependencies,
                "circular_dependencies": circular_dependencies,
            }

        except Exception as e:
            logger.error(f"Error validating dependencies for project {project_id}: {e}")
            raise DatabaseException(
                f"Error validating dependencies: {str(e)}", original_exception=e
            )

    def detect_circular_dependencies(
        self,
        db: Session,
        project_id: str,
        system_name: str,
        new_dependencies: List[str],
    ) -> List[str]:
        """Detect circular dependencies for a system.

        Args:
            db: Database session.
            project_id: The ID of the project.
            system_name: The name of the system being updated.
            new_dependencies: The new dependencies to check.

        Returns:
            List of circular dependencies detected.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            # Get all systems and their dependencies in the project
            systems = db.query(System).filter(System.project_id == project_id).all()

            # Build dependency graph
            dependency_graph = {}
            for system in systems:
                deps = system.dependencies if system.dependencies else []
                if system.name == system_name:
                    # Use the new dependencies for the system being updated
                    dependency_graph[system.name] = new_dependencies
                else:
                    dependency_graph[system.name] = deps

            # Detect circular dependencies using DFS
            circular_deps = []

            def has_circular_dependency(
                current: str, target: str, visited: set, path: List[str]
            ) -> bool:
                if current == target and len(path) > 1:
                    return True

                if current in visited:
                    return False

                visited.add(current)
                path.append(current)

                for dep in dependency_graph.get(current, []):
                    if has_circular_dependency(
                        dep, target, visited.copy(), path.copy()
                    ):
                        return True

                return False

            # Check each new dependency for circular references
            for dep in new_dependencies:
                if has_circular_dependency(dep, system_name, set(), []):
                    circular_deps.append(dep)

            return circular_deps

        except Exception as e:
            logger.error(
                f"Error detecting circular dependencies for system {system_name}: {e}"
            )
            raise DatabaseException(
                f"Error detecting circular dependencies: {str(e)}", original_exception=e
            )

    def upsert_system(
        self, db: Session, project_id: str, name: str, system_data: Dict[str, Any]
    ) -> System:
        """Create or update a system using project_id and name as natural key.

        Args:
            db: Database session.
            project_id: The ID of the project.
            name: The name of the system.
            system_data: The system data to create or update with.

        Returns:
            The created or updated system.

        Raises:
            DatabaseException: If there's an error with the database operation.
            BadRequestException: If there are validation errors.
        """
        start_time = time.time()

        try:
            id_value = system_data["id"] if system_data.get("id") else None
            existing_system = None
            if id_value:
                existing_system = self.get_by_field_or_404(db, "id", id_value)
            if existing_system:
                updated_system = self._update_system(db, 
                    existing_system, project_id, name, system_data
                )
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Updated system {name} for project {project_id} in {execution_time}ms"
                )
                return updated_system
            else:
                # Create new system
                created_system = self._insert_system(db, project_id, name, system_data)
                execution_time = int((time.time() - start_time) * 1000)
                logger.info(
                    f"Created system {name} for project {project_id} in {execution_time}ms"
                )
                return created_system

        except BadRequestException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error upserting system {name} for project {project_id}: {e}")
            raise DatabaseException(
                f"Error upserting system: {str(e)}", original_exception=e
            )

    def _insert_system(
        self, db: Session, project_id: str, name: str, system_data: Dict[str, Any]
    ):
        self._validate_upsert(db, project_id, name, system_data)
        system_data["project_id"] = project_id

        new_system = System(**system_data)
        db.add(new_system)
        db.commit()
        db.refresh(new_system)
        return new_system

    def _update_system(
        self,
        db: Session,
        existing_system,
        project_id: str,
        name: str,
        system_data: Dict[str, Any],
    ):
        self._validate_upsert(db, project_id, name, system_data)
        for field, value in system_data.items():
            if hasattr(existing_system, field) and field != "project_id":
                setattr(existing_system, field, value)

        db.add(existing_system)
        db.commit()
        db.refresh(existing_system)
        return existing_system

    def _validate_upsert(
        self, db: Session, project_id: str, name: str, system_data: Dict[str, Any]
    ):
        # Check for circular dependencies if dependencies are provided
        if "dependencies" in system_data and system_data["dependencies"]:
            circular_deps = self.detect_circular_dependencies(
                db, project_id, name, system_data["dependencies"]
            )
            if circular_deps:
                raise BadRequestException(
                    f"Circular dependencies detected: {', '.join(circular_deps)}"
                )
        system_name_exists = self.get_by_project_and_name(db, project_id, name)

        if system_name_exists and system_data.get('id') and system_data.get('id') != system_name_exists.id:
            raise DatabaseException(
                f"Error detecting circular dependencies: {name} already exists"
            )

    def delete_by_project_and_name(
        self, db: Session, project_id: str, name: str
    ) -> bool:
        """Delete a system by project ID and name.

        Args:
            db: Database session.
            project_id: The ID of the project.
            name: The name of the system.

        Returns:
            True if the system was deleted, False if not found.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            system = self.get_by_project_and_name(db, project_id, name)
            if system:
                db.delete(system)
                db.commit()
                logger.info(f"Deleted system {name} from project {project_id}")
                return True
            return False

        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting system {name} from project {project_id}: {e}")
            raise DatabaseException(
                f"Error deleting system: {str(e)}", original_exception=e
            )

    def get_systems_by_type(
        self,
        db: Session,
        project_id: str,
        system_type: SystemType,
        skip: int = 0,
        limit: int = 100,
    ) -> List[System]:
        """Get systems by project and type.

        Args:
            db: Database session.
            project_id: The ID of the project.
            system_type: The type of systems to retrieve.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of systems of the specified type.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(System).filter(
                and_(System.project_id == project_id, System.type == system_type)
            )
            return query.order_by(System.name).offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(
                f"Error retrieving {system_type.value} systems for project {project_id}: {e}"
            )
            raise DatabaseException(
                f"Error retrieving systems by type: {str(e)}", original_exception=e
            )

    def get_systems_with_dependencies(
        self, db: Session, project_id: str, skip: int = 0, limit: int = 100
    ) -> List[System]:
        """Get systems that have dependencies.

        Args:
            db: Database session.
            project_id: The ID of the project.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of systems with dependencies.

        Raises:
            DatabaseException: If there's an error with the database operation.
        """
        try:
            query = db.query(System).filter(
                and_(
                    System.project_id == project_id,
                    System.dependencies.isnot(None),
                    func.json_array_length(System.dependencies) > 0,
                )
            )
            return query.order_by(System.name).offset(skip).limit(limit).all()

        except Exception as e:
            logger.error(
                f"Error retrieving systems with dependencies for project {project_id}: {e}"
            )
            raise DatabaseException(
                f"Error retrieving systems with dependencies: {str(e)}",
                original_exception=e,
            )


system_repository = SystemRepository()
