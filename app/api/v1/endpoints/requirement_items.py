"""RequirementItem API endpoints."""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.requirement_item_service import RequirementItemService
from app.repositories.requirement_item_repository import RequirementItemRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.requirement_document_repository import RequirementDocumentRepository
from app.api.schemas.requirements import (
    # RequirementItemCreate,
    # RequirementItemUpdate,
    RequirementItemUpsert,
    RequirementItemBatchUpsert,
    RequirementItemBatchUpsertResponse,
    RequirementItemResponse,
    RequirementItemStatusUpdate,
    RequirementItemStatus,
    RequirementItemPriority
)
from app.core.exceptions import NotFoundException, BadRequestException
from app.api.dependencies import get_sse_manager, get_llm_streaming_service


router = APIRouter(tags=["Requirement Items"])


def get_requirement_item_repository() -> RequirementItemRepository:
    """Get requirement item repository dependency."""
    return RequirementItemRepository()


def get_project_repository() -> ProjectRepository:
    """Get project repository dependency."""
    return ProjectRepository()


def get_requirement_document_repository(db: Session = Depends(get_db)) -> RequirementDocumentRepository:
    """Get requirement document repository dependency."""
    return RequirementDocumentRepository()


def get_requirement_item_service(db: Session = Depends(get_db)
) -> RequirementItemService:
    """Get requirement item service dependency."""
    return RequirementItemService(db)


# @router.post(
#     "",
#     response_model=RequirementItemResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new requirement item",
#     description="Create a new requirement item with the provided data."
# )
# def create_requirement_item(
#     item_data: RequirementItemCreate = Body(..., description="The requirement item data"),
#     service: RequirementItemService = Depends(get_requirement_item_service)
# ):
#     """Create a new requirement item.
    
#     Args:
#         item_data: The requirement item data.
#         service: The requirement item service.
        
#     Returns:
#         The created requirement item.
        
#     Raises:
#         HTTPException: If the project doesn't exist or data is invalid.
#     """
#     try:
#         return service.create_requirement_item(item_data)
#     except NotFoundException as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except BadRequestException as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/requirement-items",
    response_model=List[RequirementItemResponse],
    status_code=status.HTTP_200_OK,
    summary="List requirement items",
    description="Get a list of requirement items with optional filtering and pagination."
)
def list_requirement_items(
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[RequirementItemStatus] = Query(None, description="Filter by status"),
    priority: Optional[RequirementItemPriority] = Query(None, description="Filter by priority"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """List requirement items with optional filtering.
    
    Args:
        project_id: Optional project ID filter.
        status: Optional status filter.
        priority: Optional priority filter (not implemented in service yet).
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        service: The requirement item service.
        
    Returns:
        List of requirement items.
        
    Raises:
        HTTPException: If parameters are invalid or project doesn't exist.
    """
    try:
        # Note: Priority filtering is not implemented in service yet
        return service.list_requirement_items(
            db,
            project_id=project_id,
            status=status,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/requirement-items/{item_id}",
    response_model=RequirementItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a requirement item by ID",
    description="Get a specific requirement item by its ID."
)
def get_requirement_item(
    item_id: int = Path(..., description="The ID of the requirement item"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Get a requirement item by ID.
    
    Args:
        item_id: The ID of the requirement item.
        service: The requirement item service.
        
    Returns:
        The requirement item.
        
    Raises:
        HTTPException: If the requirement item is not found.
    """
    try:
        return service.get_requirement_item(item_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



@router.post(
    "/projects/{project_id}/requirement-items",
    response_model=RequirementItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Create or update a requirement item",
    description="Create a new requirement item or update an existing one (upsert operation)."
)
def upsert_adr(
    project_id: str = Path(..., description="The ID of the project"),
    item_data: RequirementItemUpsert = ...,
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Create or update a requirement item (upsert operation).
    
    Args:
        project_id: The ID of the project.
        adr_data: The requirement item  data containing title, description, priority and optional id.
        service: The requirement item service.
        
    Returns:
        The created or updated requirement item.
        
    Raises:
        NotFoundException: If the project or requirement item (for update) is not found.

    """
    try:
        return service.upsert_requirement_item(project_id, item_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")        


# @router.post(
#     "/projects/{project_id}/requirement-items",
#     response_model=RequirementItemResponse,
#     status_code=status.HTTP_200_OK,
#     summary="Create or update a requirement item",
#     description="Create a new requirement item or update an existing one (upsert operation)."
# )
# def upsert_requirement_item(
#     project_id: str = Path(..., description="The ID of the project"),
#     item_data: RequirementItemUpsert = Body(..., description="The requirement item data"),
#     item_id: Optional[int] = Query(None, description="The ID of the requirement item to update (omit for create)"),
#     service: RequirementItemService = Depends(get_requirement_item_service)
# ):
#     """Create or update a requirement item (upsert operation).
    
#     Args:
#         item_data: The requirement item data.
#         item_id: Optional ID of the requirement item to update (omit for create).
#         service: The requirement item service.
        
#     Returns:
#         The created or updated requirement item.
        
#     Raises:
#         HTTPException: If the project doesn't exist, data is invalid, or other errors occur.
#     """
#     try:
#         result = service.upsert_requirement_item(item_id, item_data)
#         return result
#     except NotFoundException as e:
#         raise HTTPException(status_code=404, detail=str(e))
#     except BadRequestException as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/requirement-items/upsert/{item_id}",
    response_model=RequirementItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a specific requirement item",
    description="Update an existing requirement item with the provided data."
)
def upsert_requirement_item_by_id(
    item_id: int = Path(..., description="The ID of the requirement item to update"),
    item_data: RequirementItemUpsert = Body(..., description="The requirement item data"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Update a specific requirement item (upsert operation).
    
    Args:
        item_id: The ID of the requirement item to update.
        item_data: The requirement item data.
        service: The requirement item service.
        
    Returns:
        The updated requirement item.
        
    Raises:
        HTTPException: If the requirement item is not found, data is invalid, or other errors occur.
    """
    try:
        return service.upsert_requirement_item(item_id, item_data)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post(
    "/requirement-items/batch-upsert",
    response_model=RequirementItemBatchUpsertResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch upsert requirement items",
    description="Create or update multiple requirement items in a single operation."
)
def batch_upsert_requirement_items(
    batch_data: RequirementItemBatchUpsert = Body(..., description="The batch upsert data"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Batch upsert requirement items.
    
    This endpoint allows you to create or update multiple requirement items in a single
    API call. Each item in the batch should include an 'id' field and the upsert data.
    
    Args:
        batch_data: The batch upsert data containing list of items.
        service: The requirement item service.
        
    Returns:
        Batch upsert response with success/error counts and detailed results.
        
    Raises:
        HTTPException: If there are validation errors or other issues.
    """
    try:
        result = service.batch_upsert_requirement_items(batch_data)
        return RequirementItemBatchUpsertResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete(
    "/requirement-items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a requirement item",
    description="Delete an existing requirement item."
)
def delete_requirement_item(
    item_id: int = Path(..., description="The ID of the requirement item"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Delete a requirement item.
    
    Args:
        item_id: The ID of the requirement item.
        service: The requirement item service.
        
    Raises:
        HTTPException: If the requirement item is not found.
    """
    try:
        service.delete_requirement_item(item_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/requirement-items/{item_id}/status",
    response_model=RequirementItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Update requirement item status",
    description="Update the status of a specific requirement item."
)
def update_requirement_item_status(
    item_id: int = Path(..., description="The ID of the requirement item"),
    status_data: RequirementItemStatusUpdate = Body(..., description="The new status"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Update requirement item status.
    
    Args:
        item_id: The ID of the requirement item.
        status_data: The new status data.
        service: The requirement item service.
        
    Returns:
        The updated requirement item.
        
    Raises:
        HTTPException: If the requirement item is not found or status transition is invalid.
    """
    try:
        return service.update_status(item_id, status_data.status)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/projects/{project_id}/requirement-items/summary",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get project requirement items status summary",
    description="Get a summary of requirement items by status for a specific project."
)
def get_project_status_summary(
    project_id: str = Path(..., description="The ID of the project"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Get project requirement items status summary.
    
    Args:
        project_id: The ID of the project.
        service: The requirement item service.
        
    Returns:
        Dictionary with status counts.
        
    Raises:
        HTTPException: If the project is not found.
    """
    try:
        return service.get_project_status_summary(project_id)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/projects/{project_id}/requirement-items/search",
    response_model=List[RequirementItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Search requirement items by title",
    description="Search requirement items by title within a specific project."
)
def search_requirement_items(
    project_id: str = Path(..., description="The ID of the project"),
    q: str = Query(..., description="Search term for requirement item titles"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Search requirement items by title.
    
    Args:
        project_id: The ID of the project.
        q: Search term.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        service: The requirement item service.
        
    Returns:
        List of matching requirement items.
        
    Raises:
        HTTPException: If the project is not found or search term is invalid.
    """
    try:
        return service.search_requirement_items(project_id, q, skip, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.patch(
    "/requirement-items/bulk/status",
    response_model=List[RequirementItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Bulk update requirement item status",
    description="Update the status of multiple requirement items at once."
)
def bulk_update_requirement_item_status(
    item_ids: List[int] = Body(..., description="List of requirement item IDs"),
    status: RequirementItemStatus = Body(..., description="The new status"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Bulk update requirement item status.
    
    Args:
        item_ids: List of requirement item IDs.
        status: The new status.
        service: The requirement item service.
        
    Returns:
        List of updated requirement items.
        
    Raises:
        HTTPException: If any requirement item is not found or status transition is invalid.
    """
    try:
        return service.bulk_update_status(item_ids, status)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get(
    "/projects/{project_id}/requirement-items/by-status",
    response_model=List[RequirementItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get requirement items by multiple statuses",
    description="Get requirement items for a project filtered by multiple statuses."
)
def get_requirement_items_by_status(
    project_id: str = Path(..., description="The ID of the project"),
    statuses: List[RequirementItemStatus] = Query(..., description="List of statuses to filter by"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Get requirement items by multiple statuses.
    
    Args:
        project_id: The ID of the project.
        statuses: List of statuses to filter by.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        service: The requirement item service.
        
    Returns:
        List of requirement items.
        
    Raises:
        HTTPException: If the project is not found or parameters are invalid.
    """
    try:
        return service.get_requirement_items_by_status(project_id, statuses, skip, limit)
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Additional utility endpoints for better API usability
@router.get(
    "/projects/{project_id}/requirement-items",
    response_model=List[RequirementItemResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all requirement items for a project",
    description="Get all requirement items for a specific project with pagination."
)
def get_project_requirement_items(
    project_id: str = Path(..., description="The ID of the project"),
    status: Optional[RequirementItemStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: RequirementItemService = Depends(get_requirement_item_service)
):
    """Get all requirement items for a project.
    
    This is a convenience endpoint that's equivalent to calling the main list endpoint
    with a project_id filter.
    
    Args:
        project_id: The ID of the project.
        status: Optional status filter.
        skip: Number of records to skip.
        limit: Maximum number of records to return.
        service: The requirement item service.
        
    Returns:
        List of requirement items.
        
    Raises:
        HTTPException: If the project is not found or parameters are invalid.
    """
    try:
        return service.list_requirement_items(
            project_id=project_id,
            status=status,
            skip=skip,
            limit=limit
        )
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# AI-Powered Requirement Suggestions Endpoint
@router.get(
    "/projects/{project_id}/requirement-items/suggestions",
    summary="Stream AI-powered requirement suggestions",
    description="Generate and stream AI-powered requirement item suggestions based on existing requirements document."
)
async def stream_requirement_suggestions(
    request: Request,
    project_id: str = Path(..., description="The ID of the project"),
    max_suggestions: int = Query(default=10, ge=1, le=50, description="Maximum number of suggestions to generate"),
    db: Session = Depends(get_db),
    sse_manager = Depends(get_sse_manager),
    llm_streaming_service = Depends(get_llm_streaming_service),
    requirement_document_repository = Depends(get_requirement_document_repository),
    project_repository: ProjectRepository = Depends(get_project_repository)
):
    """Stream AI-powered requirement suggestions via SSE.
    
    This endpoint establishes an SSE connection and streams requirement item suggestions
    generated by AI based on the latest requirements document for the project.
    
    Args:
        request: The FastAPI request object.
        project_id: The ID of the project to generate suggestions for.
        max_suggestions: Maximum number of suggestions to generate (1-50).
        db: Database session.
        sse_manager: SSE manager for streaming.
        llm_streaming_service: LLM streaming service.
        requirement_document_repository: Repository for requirement documents.
        project_repository: Repository for projects.
        
    Returns:
        EventSourceResponse for SSE streaming.
        
    Raises:
        HTTPException: If project not found, no requirements document, or other errors.
    """
    from fastapi.responses import StreamingResponse
    from app.services.requirement_suggestion_service import RequirementSuggestionService
    from app.core.exceptions import LLMException
    import asyncio
    import json
    
    try:
        # Create the suggestion service
        suggestion_service = RequirementSuggestionService(
            llm_streaming_service,
            requirement_document_repository,
            project_repository,
            sse_manager
        )
        
        # Register SSE client
        client_id, sse_response = await sse_manager.register_client(request, "requirement_suggestions")
        
        # Start suggestion generation in background
        async def generate_suggestions():
            try:
                await suggestion_service.stream_requirement_suggestions(
                    db, client_id, project_id, max_suggestions
                )
            except (NotFoundException, BadRequestException, LLMException) as e:
                # Send error event
                await sse_manager.send_event(
                    client_id,
                    "suggestion.error",
                    {
                        "message": str(e),
                        "project_id": project_id,
                        "error_type": type(e).__name__
                    }
                )
            except Exception as e:
                # Send unexpected error event
                await sse_manager.send_event(
                    client_id,
                    "suggestion.error",
                    {
                        "message": "An unexpected error occurred",
                        "project_id": project_id,
                        "error_type": "unexpected_error"
                    }
                )
        
        # Start the background task
        asyncio.create_task(generate_suggestions())
        
        return sse_response
        
    except NotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except BadRequestException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Health and Performance Monitoring Endpoints
@router.get(
    "/requirement-items/health",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get requirement items system health",
    description="Get health status and performance metrics for the requirement items system."
)
def get_requirement_items_health(
    db: Session = Depends(get_db)
):
    """Get requirement items system health status.
    
    Args:
        db: Database session.
        
    Returns:
        Health status and metrics.
    """
    try:
        from app.core.monitoring.requirement_items import get_health_status
        from app.core.performance.requirement_items import get_performance_optimizer
        
        # Get health metrics
        health_status = get_health_status()
        
        # Get performance analysis
        optimizer = get_performance_optimizer(db)
        performance_analysis = optimizer.analyze_query_performance()
        
        return {
            "status": health_status["status"],
            "health_metrics": health_status,
            "performance_analysis": performance_analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting health status: {str(e)}")


@router.post(
    "/requirement-items/performance/optimize",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Optimize requirement items performance",
    description="Run performance optimization tasks for the requirement items system."
)
def optimize_requirement_items_performance(
    create_indexes: bool = Query(default=True, description="Create missing performance indexes"),
    vacuum_db: bool = Query(default=False, description="Vacuum database to reclaim space"),
    db: Session = Depends(get_db)
):
    """Optimize requirement items system performance.
    
    Args:
        create_indexes: Whether to create missing performance indexes.
        vacuum_db: Whether to vacuum the database.
        db: Database session.
        
    Returns:
        Optimization results.
    """
    try:
        from app.core.performance.requirement_items import get_performance_optimizer
        
        optimizer = get_performance_optimizer(db)
        results = {}
        
        if create_indexes:
            results["index_creation"] = optimizer.create_performance_indexes()
        
        if vacuum_db:
            results["vacuum"] = optimizer.vacuum_database()
        
        # Get updated performance analysis
        results["performance_analysis"] = optimizer.analyze_query_performance()
        
        return {
            "message": "Performance optimization completed",
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing performance: {str(e)}")


@router.get(
    "/requirement-items/performance/analysis/{project_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Get project-specific performance analysis",
    description="Get performance analysis for a specific project's requirement items."
)
def get_project_performance_analysis(
    project_id: str = Path(..., description="The ID of the project"),
    db: Session = Depends(get_db)
):
    """Get performance analysis for a specific project.
    
    Args:
        project_id: The ID of the project.
        db: Database session.
        
    Returns:
        Project-specific performance analysis.
    """
    try:
        from app.core.performance.requirement_items import get_performance_optimizer
        
        optimizer = get_performance_optimizer(db)
        analysis = optimizer.optimize_project_queries(project_id)
        
        return {
            "project_analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing project performance: {str(e)}")