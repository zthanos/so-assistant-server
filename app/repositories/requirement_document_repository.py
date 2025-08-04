"""Repository for versioned requirements documents."""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_

from app.domain.models.requirements import RequirementDocument
from app.api.schemas.requirements import RequirementDocumentCreate
from app.core.exceptions import NotFoundException
from app.repositories.base import CRUDRepository

logger = logging.getLogger(__name__)


class RequirementDocumentRepository(CRUDRepository[RequirementDocument, RequirementDocumentCreate, RequirementDocumentCreate]):
    """Repository for managing versioned requirements documents."""
    
    def __init__(self):
        """Initialize the repository."""
        super().__init__(RequirementDocument)
    
    def create_with_version(
        self, 
        db: Session, 
        obj_in: RequirementDocumentCreate
    ) -> RequirementDocument:
        """Create new version of requirements document.
        
        This method automatically determines the next version number for the project
        and creates a new requirements document with that version.
        
        Args:
            db: Database session
            obj_in: Requirements document creation data
            
        Returns:
            Created requirements document with version number
            
        Raises:
            Exception: If database operation fails
        """
        try:
            # Get the next version number for this project
            next_version = self.get_next_version(db, obj_in.project_id)
            
            # Create the document with version
            db_obj = RequirementDocument(
                project_id=obj_in.project_id,
                content=obj_in.content,
                version=next_version,
                status=obj_in.status,
                source_type=obj_in.source_type,
                original_filename=obj_in.original_filename
            )
            
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            
            logger.info(f"Created requirements document version {next_version} for project {obj_in.project_id}")
            return db_obj
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create requirements document: {e}")
            raise
    
    def get_next_version(self, db: Session, project_id: str) -> int:
        """Get the next version number for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            Next version number (starting from 1)
        """
        # Get the highest version number for this project
        max_version = db.query(func.max(RequirementDocument.version)).filter(
            RequirementDocument.project_id == project_id
        ).scalar()
        
        # Return next version (1 if no versions exist)
        return (max_version or 0) + 1
    
    def get_latest_version(
        self, 
        db: Session, 
        project_id: str
    ) -> Optional[RequirementDocument]:
        """Get latest version of requirements document for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            Latest requirements document or None if not found
        """
        return db.query(RequirementDocument).filter(
            RequirementDocument.project_id == project_id
        ).order_by(desc(RequirementDocument.version)).first()
    
    def get_by_version(
        self, 
        db: Session, 
        project_id: str, 
        version: int
    ) -> Optional[RequirementDocument]:
        """Get specific version of requirements document.
        
        Args:
            db: Database session
            project_id: ID of the project
            version: Version number
            
        Returns:
            Requirements document with specified version or None if not found
        """
        return db.query(RequirementDocument).filter(
            and_(
                RequirementDocument.project_id == project_id,
                RequirementDocument.version == version
            )
        ).first()
    
    def get_by_version_or_404(
        self,
        db: Session,
        project_id: str,
        version: int
    ) -> RequirementDocument:
        """Get specific version of requirements document or raise 404.
        
        Args:
            db: Database session
            project_id: ID of the project
            version: Version number
            
        Returns:
            Requirements document with specified version
            
        Raises:
            NotFoundException: If document not found
        """
        document = self.get_by_version(db, project_id, version)
        if not document:
            raise NotFoundException(
                f"Requirements document version {version} not found for project {project_id}",
                resource_type="RequirementDocument",
                resource_id=f"{project_id}/v{version}"
            )
        return document
    
    def get_all_versions(
        self,
        db: Session,
        project_id: str,
        skip: int = 0,
        limit: int = 100,
        order_desc: bool = True
    ) -> List[RequirementDocument]:
        """Get all versions of requirements documents for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            skip: Number of records to skip
            limit: Maximum number of records to return
            order_desc: If True, order by version descending (newest first)
            
        Returns:
            List of requirements documents ordered by version
        """
        query = db.query(RequirementDocument).filter(
            RequirementDocument.project_id == project_id
        )
        
        if order_desc:
            query = query.order_by(desc(RequirementDocument.version))
        else:
            query = query.order_by(RequirementDocument.version)
        
        return query.offset(skip).limit(limit).all()
    
    def get_version_count(self, db: Session, project_id: str) -> int:
        """Get total number of versions for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            Total number of versions
        """
        return db.query(RequirementDocument).filter(
            RequirementDocument.project_id == project_id
        ).count()
    
    def get_versions_by_status(
        self,
        db: Session,
        project_id: str,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[RequirementDocument]:
        """Get versions filtered by status.
        
        Args:
            db: Database session
            project_id: ID of the project
            status: Document status to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of requirements documents with specified status
        """
        return db.query(RequirementDocument).filter(
            and_(
                RequirementDocument.project_id == project_id,
                RequirementDocument.status == status
            )
        ).order_by(desc(RequirementDocument.version)).offset(skip).limit(limit).all()
    
    def get_versions_by_source_type(
        self,
        db: Session,
        project_id: str,
        source_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[RequirementDocument]:
        """Get versions filtered by source type.
        
        Args:
            db: Database session
            project_id: ID of the project
            source_type: Source type to filter by
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of requirements documents with specified source type
        """
        return db.query(RequirementDocument).filter(
            and_(
                RequirementDocument.project_id == project_id,
                RequirementDocument.source_type == source_type
            )
        ).order_by(desc(RequirementDocument.version)).offset(skip).limit(limit).all()
    
    def update_status(
        self,
        db: Session,
        document_id: int,
        status: str
    ) -> RequirementDocument:
        """Update the status of a requirements document.
        
        Args:
            db: Database session
            document_id: ID of the document to update
            status: New status value
            
        Returns:
            Updated requirements document
            
        Raises:
            NotFoundException: If document not found
        """
        document = self.get_or_404(db, document_id)
        document.status = status
        db.commit()
        db.refresh(document)
        
        logger.info(f"Updated requirements document {document_id} status to {status}")
        return document
    
    def delete_version(
        self,
        db: Session,
        project_id: str,
        version: int
    ) -> bool:
        """Delete a specific version of requirements document.
        
        Args:
            db: Database session
            project_id: ID of the project
            version: Version number to delete
            
        Returns:
            True if deleted, False if not found
        """
        document = self.get_by_version(db, project_id, version)
        if document:
            db.delete(document)
            db.commit()
            logger.info(f"Deleted requirements document version {version} for project {project_id}")
            return True
        return False
    
    def get_version_info_summary(
        self,
        db: Session,
        project_id: str
    ) -> dict:
        """Get summary information about versions for a project.
        
        Args:
            db: Database session
            project_id: ID of the project
            
        Returns:
            Dictionary with version summary information
        """
        # Get basic counts
        total_versions = self.get_version_count(db, project_id)
        
        if total_versions == 0:
            return {
                "total_versions": 0,
                "latest_version": None,
                "status_counts": {},
                "source_type_counts": {}
            }
        
        # Get latest version
        latest = self.get_latest_version(db, project_id)
        
        # Get status counts
        status_counts = db.query(
            RequirementDocument.status,
            func.count(RequirementDocument.id)
        ).filter(
            RequirementDocument.project_id == project_id
        ).group_by(RequirementDocument.status).all()
        
        # Get source type counts
        source_counts = db.query(
            RequirementDocument.source_type,
            func.count(RequirementDocument.id)
        ).filter(
            RequirementDocument.project_id == project_id
        ).group_by(RequirementDocument.source_type).all()
        
        return {
            "total_versions": total_versions,
            "latest_version": latest.version if latest else None,
            "status_counts": {status: count for status, count in status_counts},
            "source_type_counts": {source: count for source, count in source_counts}
        }


# Create singleton instance
requirement_document_repository = RequirementDocumentRepository()