"""RequirementItem service implementation."""

import logging
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.repositories.requirement_item_repository import requirement_item_repository
from app.repositories.project_repository import project_repository
from app.domain.models.requirements import RequirementItem, RequirementItemStatus
from app.api.schemas.requirements import (
    RequirementItemCreate,
    RequirementItemUpdate,
    RequirementItemUpsert,
    RequirementItemBatchUpsert,
)
from app.core.exceptions import (
    NotFoundException,
    BadRequestException,
    DatabaseException,
)

logger = logging.getLogger(__name__)


class RequirementItemService:
    """Service for requirement item operations with business logic."""

    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with dependencies.

        Args:
            db: The database session.
        """
        self.db = db
        self.repository = requirement_item_repository
        self.project_repository = project_repository

    def create_requirement_item(
        self, db: Session, item_data: RequirementItemCreate
    ) -> RequirementItem:
        """Create a new requirement item with project validation.

        Args:
            item_data: The requirement item creation data.

        Returns:
            The created requirement item.

        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If the item data is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(
            f"Creating requirement item for project {item_data.project_id}: {item_data.title}"
        )

        try:
            # Validate that the project exists
            project = self.project_repository.get(db, item_data.project_id)
            if not project:
                logger.warning(
                    f"Attempted to create requirement item for non-existent project: {item_data.project_id}"
                )
                raise NotFoundException(
                    f"Project with id {item_data.project_id} not found",
                    resource_type="Project",
                    resource_id=item_data.project_id,
                )

            # Create the requirement item
            created_item = self.repository.create(db, obj_in=item_data)
            logger.info(
                f"Successfully created requirement item {created_item.id} for project {item_data.project_id}"
            )

            # Log audit trail
            logger.info(
                f"AUDIT: RequirementItem created - ID: {created_item.id}, Project: {item_data.project_id}, "
                f"Title: {item_data.title}, Priority: {item_data.priority}, Status: {created_item.status.value}"
            )

            return created_item

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(
                f"Failed to create requirement item for project {item_data.project_id}: {str(e)}",
                exc_info=True,
            )
            raise DatabaseException(
                f"Error creating requirement item: {str(e)}", original_exception=e
            )

    def get_requirement_item(self, db: Session, item_id: int) -> RequirementItem:
        """Get requirement item by ID.

        Args:
            item_id: The ID of the requirement item.

        Returns:
            The requirement item.

        Raises:
            NotFoundException: If the requirement item doesn't exist.
        """
        return self.repository.get_or_404(db, item_id)

    def list_requirement_items(
        self,
        db: Session,
        project_id: Optional[str] = None,
        status: Optional[RequirementItemStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[RequirementItem]:
        """List requirement items with filtering.

        Args:
            project_id: Optional project ID filter.
            status: Optional status filter.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of requirement items.

        Raises:
            BadRequestException: If parameters are invalid.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate pagination parameters
            if skip < 0:
                raise BadRequestException("Skip parameter must be non-negative")
            if limit <= 0 or limit > 1000:
                raise BadRequestException("Limit parameter must be between 1 and 1000")

            if project_id:
                # Validate that the project exists
                project = self.project_repository.get(db, project_id)
                if not project:
                    raise NotFoundException(
                        f"Project with id {project_id} not found",
                        resource_type="Project",
                        resource_id=project_id,
                    )

                return self.repository.get_by_project(
                    db, project_id, status, skip, limit
                )
            else:
                # Get all items with optional status filter
                filters = {}
                if status is not None:
                    filters["status"] = status

                return self.repository.get_multi(
                    db, skip=skip, limit=limit, filters=filters if filters else None
                )

        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            raise DatabaseException(
                f"Error listing requirement items: {str(e)}", original_exception=e
            )

    def list_requirement_items_with_pagination(
        self,
        project_id: str,
        status: Optional[RequirementItemStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> Tuple[List[RequirementItem], int]:
        """List requirement items with total count for pagination.

        Args:
            project_id: The project ID.
            status: Optional status filter.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            Tuple of (items, total_count).

        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If parameters are invalid.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate pagination parameters
            if skip < 0:
                raise BadRequestException("Skip parameter must be non-negative")
            if limit <= 0 or limit > 1000:
                raise BadRequestException("Limit parameter must be between 1 and 1000")

            # Validate that the project exists
            project = self.project_repository.get(self.repository.db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id,
                )

            return self.repository.get_by_project_with_pagination_info(
                project_id, status, skip, limit
            )

        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            raise DatabaseException(
                f"Error listing requirement items with pagination: {str(e)}",
                original_exception=e,
            )

    # def update_requirement_item(
    #     self,
    #     item_id: int,
    #     item_data: RequirementItemUpdate
    # ) -> RequirementItem:
    #     """Update requirement item.

    #     Args:
    #         item_id: The ID of the requirement item.
    #         item_data: The update data.

    #     Returns:
    #         The updated requirement item.

    #     Raises:
    #         NotFoundException: If the requirement item doesn't exist.
    #         BadRequestException: If the update data is invalid.
    #         DatabaseException: If there's a database error.
    #     """
    #     try:
    #         # Get the existing item
    #         existing_item = self.repository.get_or_404(self.repository.db, item_id)

    #         # Validate status transitions if status is being updated
    #         if item_data.status is not None:
    #             self._validate_status_transition(existing_item.status, item_data.status)

    #         # Update the item
    #         return self.repository.update_by_id(
    #             self.repository.db,
    #             id=item_id,
    #             obj_in=item_data
    #         )

    #     except (NotFoundException, BadRequestException):
    #         raise
    #     except Exception as e:
    #         raise DatabaseException(
    #             f"Error updating requirement item {item_id}: {str(e)}",
    #             original_exception=e
    #         )

    def upsert_requirement_item(
        self, project_id: str, item_data: RequirementItemUpsert
    ) -> RequirementItem:
        """Create or update a requirement item (upsert operation).

        Args:
            project_id: The ID of the requirement item (None for create).
            item_data: The upsert data.

        Returns:
            The created or updated requirement item.

        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If the data is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Upserting requirement item for project {project_id}")

        try:
            # Validate that the project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            if not project:
                logger.warning(
                    f"Attempted to upsert requirement item {item_data.id} for non-existent project: {project_id}"
                )
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id,
                )

            if item_data.id is None:
                # Create new item
                create_data = RequirementItemCreate(
                    project_id=project_id,
                    title=item_data.title,
                    description=item_data.description,
                    priority=item_data.priority,
                )
                created_item = self.repository.create(self.db, obj_in=create_data)

                # Update status if provided
                if item_data.status is not None:
                    created_item = self.repository.update_status(
                        self.db, created_item.id, item_data.status
                    )

                logger.info(
                    f"AUDIT: RequirementItem created via upsert - ID: {created_item.id}, "
                    f"Project: {project_id}, Title: {item_data.title}"
                )

                return created_item
            else:
                # Update existing item
                existing_item = self.repository.get_or_404(self.db, item_data.id)

                # Validate project consistency
                if existing_item.project_id != project_id:
                    raise BadRequestException(
                        f"Cannot change project_id from {existing_item.project_id} to {project_id}"
                    )

                # Validate status transitions if status is being updated
                if (
                    item_data.status is not None
                    and item_data.status != existing_item.status.value
                ):
                    self._validate_status_transition(
                        existing_item.status, item_data.status
                    )

                # Update the item
                update_data = RequirementItemUpdate(
                    title=item_data.title,
                    description=item_data.description,
                    priority=item_data.priority,
                    status=item_data.status,
                )

                updated_item = self.repository.update_by_id(
                    self.db, id=item_data.id, obj_in=update_data
                )

                logger.info(
                    f"AUDIT: RequirementItem updated via upsert - ID: {item_data.id}, "
                    f"Project: {project_id}, Title: {item_data.title}"
                )

                return updated_item

        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            logger.error(
                f"Failed to upsert requirement item {item_data.id} for project {project_id}: {str(e)}",
                exc_info=True,
            )
            raise DatabaseException(
                f"Error upserting requirement item: {str(e)}", original_exception=e
            )

    def batch_upsert_requirement_items(
        self, batch_data: RequirementItemBatchUpsert
    ) -> Dict[str, Any]:
        """Perform batch upsert operations on multiple requirement items.

        Args:
            batch_data: The batch upsert data containing list of items.

        Returns:
            Dictionary with success/error counts and detailed results.
        """
        logger.info(f"Starting batch upsert for {len(batch_data.items)} items")

        results = []
        success_count = 0
        error_count = 0

        for item_data in batch_data.items:
            item_id = item_data["id"]
            upsert_data_dict = {k: v for k, v in item_data.items() if k != "id"}

            try:
                # Create RequirementItemUpsert object from the data
                upsert_data = RequirementItemUpsert(**upsert_data_dict)

                # Perform the upsert
                result_item = self.upsert_requirement_item(item_id, upsert_data)

                results.append(
                    {
                        "id": item_id,
                        "status": "success",
                        "item": {
                            "id": result_item.id,
                            "project_id": result_item.project_id,
                            "title": result_item.title,
                            "description": result_item.description,
                            "priority": result_item.priority.value,
                            "status": result_item.status.value,
                            "created_at": (
                                result_item.created_at.isoformat()
                                if result_item.created_at
                                else None
                            ),
                            "updated_at": (
                                result_item.updated_at.isoformat()
                                if result_item.updated_at
                                else None
                            ),
                        },
                    }
                )
                success_count += 1

            except (NotFoundException, BadRequestException, DatabaseException) as e:
                logger.warning(f"Failed to upsert item {item_id}: {str(e)}")
                results.append({"id": item_id, "status": "error", "error": str(e)})
                error_count += 1

            except Exception as e:
                logger.error(
                    f"Unexpected error upserting item {item_id}: {str(e)}",
                    exc_info=True,
                )
                results.append(
                    {
                        "id": item_id,
                        "status": "error",
                        "error": f"Unexpected error: {str(e)}",
                    }
                )
                error_count += 1

        logger.info(
            f"Batch upsert completed: {success_count} success, {error_count} errors"
        )

        return {
            "success_count": success_count,
            "error_count": error_count,
            "results": results,
        }

    def delete_requirement_item(self, item_id: int) -> None:
        """Delete requirement item.

        Args:
            item_id: The ID of the requirement item.

        Raises:
            NotFoundException: If the requirement item doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            self.repository.delete(self.repository.db, id=item_id)
        except Exception as e:
            if "not found" in str(e).lower():
                raise NotFoundException(
                    f"Requirement item with id {item_id} not found",
                    resource_type="RequirementItem",
                    resource_id=item_id,
                )
            raise DatabaseException(
                f"Error deleting requirement item {item_id}: {str(e)}",
                original_exception=e,
            )

    def update_status(
        self, item_id: int, status: RequirementItemStatus
    ) -> RequirementItem:
        """Update requirement item status with validation.

        Args:
            item_id: The ID of the requirement item.
            status: The new status.

        Returns:
            The updated requirement item.

        Raises:
            NotFoundException: If the requirement item doesn't exist.
            BadRequestException: If the status transition is invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(f"Updating status for requirement item {item_id} to {status.value}")

        try:
            # Get the existing item to validate status transition
            existing_item = self.repository.get_or_404(self.repository.db, item_id)
            old_status = existing_item.status

            # Validate status transition
            self._validate_status_transition(existing_item.status, status)

            # Update the status
            updated_item = self.repository.update_status(item_id, status)

            # Log audit trail for status change
            logger.info(
                f"AUDIT: RequirementItem status updated - ID: {item_id}, "
                f"Old Status: {old_status.value}, New Status: {status.value}, "
                f"Project: {existing_item.project_id}, Title: {existing_item.title}"
            )

            logger.info(
                f"Successfully updated status for requirement item {item_id} from {old_status.value} to {status.value}"
            )

            return updated_item

        except (NotFoundException, BadRequestException) as e:
            logger.warning(
                f"Status update failed for requirement item {item_id}: {str(e)}"
            )
            raise
        except Exception as e:
            logger.error(
                f"Failed to update status for requirement item {item_id}: {str(e)}",
                exc_info=True,
            )
            raise DatabaseException(
                f"Error updating status for requirement item {item_id}: {str(e)}",
                original_exception=e,
            )

    def get_project_status_summary(self, project_id: str) -> dict[str, int]:
        """Get status summary for a project's requirement items.

        Args:
            project_id: The ID of the project.

        Returns:
            Dictionary with status counts.

        Raises:
            NotFoundException: If the project doesn't exist.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate that the project exists
            project = self.project_repository.get(self.repository.db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id,
                )

            return self.repository.get_status_summary(project_id)

        except NotFoundException:
            raise
        except Exception as e:
            raise DatabaseException(
                f"Error getting status summary for project {project_id}: {str(e)}",
                original_exception=e,
            )

    def search_requirement_items(
        self, project_id: str, search_term: str, skip: int = 0, limit: int = 100
    ) -> List[RequirementItem]:
        """Search requirement items by title within a project.

        Args:
            project_id: The ID of the project.
            search_term: The term to search for.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of matching requirement items.

        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If parameters are invalid.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate parameters
            if not search_term or not search_term.strip():
                raise BadRequestException("Search term cannot be empty")
            if skip < 0:
                raise BadRequestException("Skip parameter must be non-negative")
            if limit <= 0 or limit > 1000:
                raise BadRequestException("Limit parameter must be between 1 and 1000")

            # Validate that the project exists
            project = self.project_repository.get(self.repository.db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id,
                )

            return self.repository.search_by_title(
                project_id, search_term.strip(), skip, limit
            )

        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            raise DatabaseException(
                f"Error searching requirement items: {str(e)}", original_exception=e
            )

    def bulk_update_status(
        self, item_ids: List[int], status: RequirementItemStatus
    ) -> List[RequirementItem]:
        """Update status for multiple requirement items.

        Args:
            item_ids: List of requirement item IDs.
            status: The new status.

        Returns:
            List of updated requirement items.

        Raises:
            BadRequestException: If parameters are invalid.
            DatabaseException: If there's a database error.
        """
        logger.info(
            f"Bulk updating status for {len(item_ids)} requirement items to {status.value}"
        )

        try:
            # Validate parameters
            if not item_ids:
                logger.warning("Attempted bulk status update with empty item IDs list")
                raise BadRequestException("Item IDs list cannot be empty")
            if len(item_ids) > 100:
                logger.warning(
                    f"Attempted bulk status update with {len(item_ids)} items (max 100)"
                )
                raise BadRequestException("Cannot update more than 100 items at once")

            # Validate that all items exist and check status transitions
            existing_items = []
            for item_id in item_ids:
                existing_item = self.repository.get_or_404(self.repository.db, item_id)
                self._validate_status_transition(existing_item.status, status)
                existing_items.append(existing_item)

            # Perform bulk update
            updated_items = self.repository.bulk_update_status(item_ids, status)

            # Log audit trail for bulk update
            for existing_item in existing_items:
                logger.info(
                    f"AUDIT: RequirementItem bulk status update - ID: {existing_item.id}, "
                    f"Old Status: {existing_item.status.value}, New Status: {status.value}, "
                    f"Project: {existing_item.project_id}, Title: {existing_item.title}"
                )

            logger.info(
                f"Successfully bulk updated status for {len(updated_items)} requirement items to {status.value}"
            )

            return updated_items

        except (NotFoundException, BadRequestException) as e:
            logger.warning(f"Bulk status update failed for items {item_ids}: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"Failed to bulk update status for items {item_ids}: {str(e)}",
                exc_info=True,
            )
            raise DatabaseException(
                f"Error bulk updating status for items {item_ids}: {str(e)}",
                original_exception=e,
            )

    def _validate_status_transition(
        self, current_status: RequirementItemStatus, new_status: RequirementItemStatus
    ) -> None:
        """Validate that a status transition is allowed.

        Args:
            current_status: The current status.
            new_status: The desired new status.

        Raises:
            BadRequestException: If the transition is not allowed.
        """
        # Define allowed transitions
        allowed_transitions = {
            RequirementItemStatus.new: [
                RequirementItemStatus.accepted.value,
                RequirementItemStatus.rejected.value,
            ],
            RequirementItemStatus.accepted: [
                RequirementItemStatus.rejected.value,
                RequirementItemStatus.new.value,  # Allow reopening
            ],
            RequirementItemStatus.rejected: [
                RequirementItemStatus.new.value,  # Allow reopening
                RequirementItemStatus.accepted.value,  # Allow direct acceptance
            ],
        }

        # Allow staying in the same status (no-op)
        if current_status.value == new_status.value:
            return

        # Check if transition is allowed
        if new_status not in allowed_transitions.get(current_status, []):
            raise BadRequestException(
                f"Invalid status transition from {current_status.value} to {new_status.value}"
            )

    def get_requirement_items_by_status(
        self,
        db: Session,
        project_id: str,
        statuses: List[RequirementItemStatus],
        skip: int = 0,
        limit: int = 100,
    ) -> List[RequirementItem]:
        """Get requirement items by project and multiple statuses.

        Args:
            project_id: The ID of the project.
            statuses: List of statuses to filter by.
            skip: Number of records to skip for pagination.
            limit: Maximum number of records to return.

        Returns:
            List of requirement items.

        Raises:
            NotFoundException: If the project doesn't exist.
            BadRequestException: If parameters are invalid.
            DatabaseException: If there's a database error.
        """
        try:
            # Validate parameters
            if not statuses:
                raise BadRequestException("Statuses list cannot be empty")
            if skip < 0:
                raise BadRequestException("Skip parameter must be non-negative")
            if limit <= 0 or limit > 1000:
                raise BadRequestException("Limit parameter must be between 1 and 1000")

            # Validate that the project exists
            project = self.project_repository.get(db, project_id)
            if not project:
                raise NotFoundException(
                    f"Project with id {project_id} not found",
                    resource_type="Project",
                    resource_id=project_id,
                )

            return self.repository.get_by_project_and_status(
                db, project_id, statuses, skip, limit
            )

        except (NotFoundException, BadRequestException):
            raise
        except Exception as e:
            raise DatabaseException(
                f"Error getting requirement items by status: {str(e)}",
                original_exception=e,
            )

# Create a singleton instance
requirement_item_service = RequirementItemService()