"""Requirement Document API endpoints.

This module provides API endpoints for managing versioned requirements documents.
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Path, Query, HTTPException, status, Request, File, UploadFile
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import (
    get_pagination_params_dependency, 
    get_search_params, 
    get_filter_params
)
from app.services.requirement_document_service import RequirementDocumentService
from app.domain.models.requirements import RequirementDocumentStatus, SourceType
from app.api.schemas.requirements import (
    RequirementDocumentCreate,
    RequirementDocumentUpsert,
    RequirementDocumentResponse,
    RequirementDocumentVersionInfo
)
from app.api.schemas.common import PaginatedResponse
from app.core.exceptions import NotFoundException, BadRequestException
from app.exceptions.pdf_exceptions import (
    PDFProcessingError,
    InvalidPDFError,
    PDFTooLargeError,
    TextExtractionError,
    pdf_exception_to_http_exception
)
from app.utils.pagination import PaginationParams
from app.utils.filtering import parse_filter_params
from app.utils.response_utils import paginated_response

router = APIRouter()

def get_requirement_document_service(db: Session = Depends(get_db)) -> RequirementDocumentService:
    """Get requirement document service instance."""
    return RequirementDocumentService(db)

@router.post(
    "/projects/{project_id}/requirements-document",
    response_model=RequirementDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update requirements document",
    description="Create a new requirements document or update an existing one with a new version using upsert logic."
)
def upsert_requirements_document(
    request: RequirementDocumentUpsert,
    project_id: str = Path(..., description="The ID of the project"),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Create or update requirements document using upsert logic.
    
    This endpoint implements upsert logic:
    - Always creates a new version with incremented version number
    - If no requirements exist for the project, creates version 1
    - If requirements already exist, creates the next version
    
    Args:
        project_id: The ID of the project
        request: The requirement document data
        service: The requirement document service
        
    Returns:
        The created or updated requirements document with version information
        
    Raises:
        HTTPException: If the project is not found or content is invalid
    """
    try:
        document = service.upsert_requirements(
            project_id=project_id,
            content=request.content,
            status=request.status,
            source_type=request.source_type or SourceType.manual,
            original_filename=request.original_filename
        )
        return document
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/requirements-document/latest",
    response_model=RequirementDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the latest requirements document",
    description="Get the latest version of requirements document for a project."
)
def get_latest_requirements_document(
    project_id: str = Path(..., description="The ID of the project"),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Get the latest requirements document.
    
    Args:
        project_id: The ID of the project
        service: The requirement document service
        
    Returns:
        The latest requirements document or empty document if none exists
        
    Raises:
        HTTPException: If the project is not found
    """
    try:
        document = service.get_latest_requirements(project_id)
        return document
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/requirements-document/{version}",
    response_model=RequirementDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get requirements document by version",
    description="Get a specific version of requirements document for a project."
)
def get_requirements_document_by_version(
    project_id: str = Path(..., description="The ID of the project"),
    version: int = Path(..., description="The version number", ge=1),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Get requirements document by version.
    
    Args:
        project_id: The ID of the project
        version: The version number
        service: The requirement document service
        
    Returns:
        The requirements document with specified version
        
    Raises:
        HTTPException: If the project or version is not found
    """
    try:
        document = service.get_requirements_by_version(project_id, version)
        return document
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/requirements-document",
    response_model=PaginatedResponse[RequirementDocumentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all requirements document versions",
    description="Get all versions of requirements documents for a project with pagination and filtering support."
)
def get_requirements_document_versions(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    pagination: PaginationParams = Depends(get_pagination_params_dependency),
    status_filter: Optional[RequirementDocumentStatus] = Query(
        None, 
        description="Filter by document status"
    ),
    source_type_filter: Optional[SourceType] = Query(
        None,
        description="Filter by source type"
    ),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Get all requirements document versions with pagination and filtering.
    
    Args:
        request: The FastAPI request object
        project_id: The ID of the project
        pagination: Pagination parameters
        status_filter: Optional status filter
        source_type_filter: Optional source type filter
        service: The requirement document service
        
    Returns:
        Paginated list of requirements document versions
        
    Raises:
        HTTPException: If the project is not found
    """
    try:
        # Get paginated requirements document versions
        result = service.get_requirements_versions(
            project_id=project_id,
            pagination=pagination,
            status_filter=status_filter,
            source_type_filter=source_type_filter
        )
        
        # Return paginated response
        return paginated_response(
            data=result.items,
            page=result.page,
            per_page=result.per_page,
            total=result.total,
            message="Requirements document versions retrieved successfully"
        )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.post(
    "/projects/{project_id}/requirements-document/upload-pdf",
    response_model=RequirementDocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload PDF requirements document",
    description="Upload a PDF file and convert it to a requirements document using LLM."
)
async def upload_requirements_pdf(
    project_id: str = Path(..., description="The ID of the project"),
    file: UploadFile = File(..., description="PDF file to upload"),
    status: Optional[RequirementDocumentStatus] = Query(
        RequirementDocumentStatus.draft,
        description="The status for the created requirements document"
    ),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Upload PDF requirements document and convert to markdown.
    
    This endpoint:
    1. Validates the uploaded PDF file
    2. Extracts text content from the PDF
    3. Converts the text to structured markdown using LLM
    4. Creates a new requirements document version
    
    Args:
        project_id: The ID of the project
        file: The PDF file to upload
        status: The status for the created document
        service: The requirement document service
        
    Returns:
        The created requirements document with converted content
        
    Raises:
        HTTPException: If upload fails, file is invalid, or processing fails
    """
    try:
        document = await service.process_pdf_upload(
            project_id=project_id,
            file=file,
            status=status
        )
        return document
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except (InvalidPDFError, PDFTooLargeError, TextExtractionError, PDFProcessingError) as e:
        raise pdf_exception_to_http_exception(e)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.patch(
    "/requirements-document/{document_id}/status",
    response_model=RequirementDocumentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update requirements document status",
    description="Update the status of a requirements document."
)
def update_requirements_document_status(
    document_id: int = Path(..., description="The ID of the requirements document"),
    status: RequirementDocumentStatus = Query(..., description="The new status"),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Update requirements document status.
    
    Args:
        document_id: The ID of the requirements document
        status: The new status
        service: The requirement document service
        
    Returns:
        The updated requirements document
        
    Raises:
        HTTPException: If the document is not found
    """
    try:
        document = service.update_requirements_status(document_id, status)
        return document
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.delete(
    "/projects/{project_id}/requirements-document/{version}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete requirements document version",
    description="Delete a specific version of requirements document."
)
def delete_requirements_document_version(
    project_id: str = Path(..., description="The ID of the project"),
    version: int = Path(..., description="The version number to delete", ge=1),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Delete requirements document version.
    
    Args:
        project_id: The ID of the project
        version: The version number to delete
        service: The requirement document service
        
    Raises:
        HTTPException: If the project is not found or version doesn't exist
    """
    try:
        deleted = service.delete_requirements_version(project_id, version)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Requirements document version {version} not found for project {project_id}"
            )
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

@router.get(
    "/projects/{project_id}/requirements-document/summary",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get requirements summary",
    description="Get summary information about requirements for a project."
)
def get_requirements_summary(
    project_id: str = Path(..., description="The ID of the project"),
    service: RequirementDocumentService = Depends(get_requirement_document_service)
):
    """Get requirements summary for a project.
    
    Args:
        project_id: The ID of the project
        service: The requirement document service
        
    Returns:
        Summary information about requirements including version counts and statistics
        
    Raises:
        HTTPException: If the project is not found
    """
    try:
        summary = service.get_requirements_summary(project_id)
        return summary
    except NotFoundException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except BadRequestException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)