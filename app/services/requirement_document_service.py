"""Service for managing versioned requirements documents."""

import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import Depends, UploadFile

from app.core.database import get_db
from app.repositories.requirement_document_repository import requirement_document_repository
from app.repositories.project_repository import ProjectRepository
from app.domain.models.requirements import RequirementDocument, RequirementDocumentStatus, SourceType
from app.api.schemas.requirements import (
    RequirementDocumentCreate,
    RequirementDocumentResponse,
    RequirementDocumentVersionInfo
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.services.langchain_pdf_processor import create_pdf_processor
from app.services.requirements_pdf_converter import RequirementsPDFConverter
from app.exceptions.pdf_exceptions import (
    PDFProcessingError,
    InvalidPDFError,
    PDFTooLargeError,
    TextExtractionError
)
from app.utils.pagination import PaginationParams, PaginationResult, Paginator

logger = logging.getLogger(__name__)


class RequirementDocumentService:
    """Service for managing versioned requirements documents."""
    
    def __init__(self, db: Session = Depends(get_db)):
        """Initialize the service with dependencies.
        
        Args:
            db: The database session.
        """
        self.db = db
        self.repository = requirement_document_repository
        self.project_repository = ProjectRepository()
        self.pdf_processor = create_pdf_processor(use_langchain=True)
        self.pdf_converter = RequirementsPDFConverter()
    
    def upsert_requirements(
        self, 
        project_id: str, 
        content: str, 
        status: RequirementDocumentStatus = RequirementDocumentStatus.draft,
        source_type: SourceType = SourceType.manual,
        original_filename: Optional[str] = None
    ) -> RequirementDocument:
        """Create or update requirements document with versioning.
        
        This method implements upsert logic - it always creates a new version
        regardless of whether requirements already exist for the project.
        
        Args:
            project_id: The ID of the project
            content: The markdown content of the requirements
            status: The status of the requirements document
            source_type: The source type (manual or pdf_upload)
            original_filename: Original filename for PDF uploads
            
        Returns:
            The created requirements document with version information
            
        Raises:
            NotFoundException: If the project is not found
            BadRequestException: If the content is invalid
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            # Validate content
            if not content or not content.strip():
                raise BadRequestException("Requirements content cannot be empty")
            
            # Create requirements document data
            requirements_data = RequirementDocumentCreate(
                project_id=project_id,
                content=content.strip(),
                status=status,
                source_type=source_type,
                original_filename=original_filename
            )
            
            # Create with automatic versioning
            document = self.repository.create_with_version(self.db, requirements_data)
            
            logger.info(
                f"Created requirements document version {document.version} for project {project_id} "
                f"(source: {source_type.value})"
            )
            
            return document
            
        except NotFoundException:
            # Re-raise project not found errors
            raise
        except BadRequestException:
            # Re-raise validation errors
            raise
        except Exception as e:
            logger.error(f"Failed to upsert requirements for project {project_id}: {e}")
            raise BadRequestException(f"Failed to create requirements document: {str(e)}")
    
    def get_latest_requirements(self, project_id: str) -> RequirementDocument:
        """Get latest requirements or return empty document.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Latest requirements document or empty document if none exists
            
        Raises:
            NotFoundException: If the project is not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            # Get latest version
            document = self.repository.get_latest_version(self.db, project_id)
            
            if document is None:
                # Return empty document
                from datetime import datetime
                
                class EmptyRequirementDocument:
                    def __init__(self):
                        self.id = 0
                        self.project_id = project_id
                        self.content = ""
                        self.version = 0
                        self.status = RequirementDocumentStatus.draft
                        self.source_type = SourceType.manual
                        self.original_filename = None
                        self.created_at = datetime.now()
                        self.updated_at = datetime.now()
                
                return EmptyRequirementDocument()
            
            return document
            
        except NotFoundException:
            # Re-raise project not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to get latest requirements for project {project_id}: {e}")
            raise BadRequestException(f"Failed to retrieve requirements: {str(e)}")
    
    def get_requirements_by_version(
        self, 
        project_id: str, 
        version: int
    ) -> RequirementDocument:
        """Get specific version of requirements document.
        
        Args:
            project_id: The ID of the project
            version: The version number
            
        Returns:
            Requirements document with specified version
            
        Raises:
            NotFoundException: If the project or version is not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            # Get specific version
            return self.repository.get_by_version_or_404(self.db, project_id, version)
            
        except NotFoundException:
            # Re-raise not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to get requirements version {version} for project {project_id}: {e}")
            raise BadRequestException(f"Failed to retrieve requirements version: {str(e)}")
    
    def get_requirements_versions(
        self,
        project_id: str,
        pagination: PaginationParams,
        status_filter: Optional[RequirementDocumentStatus] = None,
        source_type_filter: Optional[SourceType] = None
    ) -> PaginationResult[RequirementDocument]:
        """Get all versions of requirements documents with pagination and filtering.
        
        Args:
            project_id: The ID of the project
            pagination: Pagination parameters
            status_filter: Optional status filter
            source_type_filter: Optional source type filter
            
        Returns:
            Paginated result of requirements document versions
            
        Raises:
            NotFoundException: If the project is not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            # Calculate skip value
            skip = (pagination.page - 1) * pagination.per_page
            
            # Build query based on filters
            if status_filter and source_type_filter:
                # Both filters
                query = self.db.query(RequirementDocument).filter(
                    RequirementDocument.project_id == project_id,
                    RequirementDocument.status == status_filter,
                    RequirementDocument.source_type == source_type_filter
                ).order_by(RequirementDocument.version.desc())
                
                total = query.count()
                items = query.offset(skip).limit(pagination.per_page).all()
                
                return PaginationResult(
                    items=items,
                    total=total,
                    page=pagination.page,
                    per_page=pagination.per_page,
                    pages=(total + pagination.per_page - 1) // pagination.per_page,
                    has_next=pagination.page < ((total + pagination.per_page - 1) // pagination.per_page),
                    has_prev=pagination.page > 1
                )
                
            elif status_filter:
                # Status filter only
                documents = self.repository.get_versions_by_status(
                    self.db, project_id, status_filter.value, 
                    skip=skip, limit=pagination.per_page
                )
                # Convert to paginated result
                total = self.db.query(RequirementDocument).filter(
                    RequirementDocument.project_id == project_id,
                    RequirementDocument.status == status_filter
                ).count()
                return PaginationResult(
                    items=documents,
                    total=total,
                    page=pagination.page,
                    per_page=pagination.per_page,
                    pages=(total + pagination.per_page - 1) // pagination.per_page,
                    has_next=pagination.page < ((total + pagination.per_page - 1) // pagination.per_page),
                    has_prev=pagination.page > 1
                )
                
            elif source_type_filter:
                # Source type filter only
                documents = self.repository.get_versions_by_source_type(
                    self.db, project_id, source_type_filter.value,
                    skip=skip, limit=pagination.per_page
                )
                # Convert to paginated result
                total = self.db.query(RequirementDocument).filter(
                    RequirementDocument.project_id == project_id,
                    RequirementDocument.source_type == source_type_filter
                ).count()
                return PaginationResult(
                    items=documents,
                    total=total,
                    page=pagination.page,
                    per_page=pagination.per_page,
                    pages=(total + pagination.per_page - 1) // pagination.per_page,
                    has_next=pagination.page < ((total + pagination.per_page - 1) // pagination.per_page),
                    has_prev=pagination.page > 1
                )
                
            else:
                # No filters
                documents = self.repository.get_all_versions(
                    self.db, project_id,
                    skip=skip, limit=pagination.per_page
                )
                total = self.repository.get_version_count(self.db, project_id)
                return PaginationResult(
                    items=documents,
                    total=total,
                    page=pagination.page,
                    per_page=pagination.per_page,
                    pages=(total + pagination.per_page - 1) // pagination.per_page,
                    has_next=pagination.page < ((total + pagination.per_page - 1) // pagination.per_page),
                    has_prev=pagination.page > 1
                )
            
        except NotFoundException:
            # Re-raise project not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to get requirements versions for project {project_id}: {e}")
            raise BadRequestException(f"Failed to retrieve requirements versions: {str(e)}")
    
    async def process_pdf_upload(
        self,
        project_id: str,
        file: UploadFile,
        status: RequirementDocumentStatus = RequirementDocumentStatus.draft
    ) -> RequirementDocument:
        """Process uploaded PDF and convert to requirements document.
        
        Args:
            project_id: The ID of the project
            file: The uploaded PDF file
            status: The status for the created document
            
        Returns:
            Created requirements document with converted content
            
        Raises:
            NotFoundException: If the project is not found
            InvalidPDFError: If the PDF file is invalid
            PDFTooLargeError: If the PDF file is too large
            TextExtractionError: If text extraction fails
            BadRequestException: If processing fails
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            logger.info(f"Processing PDF upload for project {project_id}: {file.filename}")
            
            # Process PDF file
            pdf_text = await self.pdf_processor.process_pdf_file(file)
            
            # Convert to markdown using LLM
            project_context = f"Project: {project.name}"
            if project.description:
                project_context += f"\nDescription: {project.description}"
            
            markdown_content = await self.pdf_converter.convert_with_fallback(
                pdf_text=pdf_text,
                filename=file.filename or "uploaded.pdf",
                project_context=project_context
            )
            
            # Create requirements document
            document = self.upsert_requirements(
                project_id=project_id,
                content=markdown_content,
                status=status,
                source_type=SourceType.pdf_upload,
                original_filename=file.filename
            )
            
            logger.info(
                f"Successfully processed PDF upload for project {project_id}: "
                f"created version {document.version}"
            )
            
            return document
            
        except NotFoundException:
            # Re-raise project not found errors
            raise
        except (InvalidPDFError, PDFTooLargeError, TextExtractionError):
            # Re-raise PDF processing errors
            raise
        except Exception as e:
            logger.error(f"Failed to process PDF upload for project {project_id}: {e}")
            raise BadRequestException(f"Failed to process PDF upload: {str(e)}")
    
    def update_requirements_status(
        self,
        document_id: int,
        status: RequirementDocumentStatus
    ) -> RequirementDocument:
        """Update the status of a requirements document.
        
        Args:
            document_id: The ID of the document
            status: The new status
            
        Returns:
            Updated requirements document
            
        Raises:
            NotFoundException: If the document is not found
        """
        try:
            document = self.repository.update_status(self.db, document_id, status.value)
            logger.info(f"Updated requirements document {document_id} status to {status.value}")
            return document
            
        except NotFoundException:
            # Re-raise not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to update requirements document {document_id} status: {e}")
            raise BadRequestException(f"Failed to update document status: {str(e)}")
    
    def delete_requirements_version(
        self,
        project_id: str,
        version: int
    ) -> bool:
        """Delete a specific version of requirements document.
        
        Args:
            project_id: The ID of the project
            version: The version number to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            NotFoundException: If the project is not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            # Delete version
            deleted = self.repository.delete_version(self.db, project_id, version)
            
            if deleted:
                logger.info(f"Deleted requirements document version {version} for project {project_id}")
            
            return deleted
            
        except NotFoundException:
            # Re-raise project not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to delete requirements version {version} for project {project_id}: {e}")
            raise BadRequestException(f"Failed to delete requirements version: {str(e)}")
    
    def get_requirements_summary(self, project_id: str) -> dict:
        """Get summary information about requirements for a project.
        
        Args:
            project_id: The ID of the project
            
        Returns:
            Dictionary with requirements summary information
            
        Raises:
            NotFoundException: If the project is not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_or_404(self.db, project_id)
            
            # Get version summary
            summary = self.repository.get_version_info_summary(self.db, project_id)
            
            # Add project information
            summary["project"] = {
                "id": project.id,
                "name": project.name,
                "description": project.description
            }
            
            return summary
            
        except NotFoundException:
            # Re-raise project not found errors
            raise
        except Exception as e:
            logger.error(f"Failed to get requirements summary for project {project_id}: {e}")
            raise BadRequestException(f"Failed to get requirements summary: {str(e)}")


# Create singleton instance
requirement_document_service = RequirementDocumentService()