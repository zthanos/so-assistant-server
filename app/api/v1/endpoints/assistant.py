"""Assistant API endpoints for LLM routing and SSE responses."""
import asyncio
import logging
import time
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.api.schemas.assistant import (
    AssistantQueryRequest,
    AssistantResponse,
    SSEStartEvent,
    SSETokenEvent,
    SSEJsonEvent,
    SSEFinalEvent,
    SSEErrorEvent,
    SSEProgressEvent,
    SSEExecutionMetrics,
    StructuredAnalysisResponse
)
from app.services.agent.setup import get_agent_framework
from app.services.agent.sse_manager import agent_sse_manager
from app.services.agent.health import health_monitor
from app.core.exceptions import LLMException, NotFoundException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/assistant", tags=["assistant"])


@router.post("/projects/{project_id}/query")
async def process_assistant_query(
    project_id: str,
    request_data: AssistantQueryRequest,
    request: Request,
    background_tasks: BackgroundTasks
) -> EventSourceResponse:
    """Process assistant query with SSE streaming.
    
    This endpoint processes user queries through the LLM routing system
    and streams responses back via Server-Sent Events.
    
    Args:
        project_id: The project ID for context
        request_data: The query request data
        request: The FastAPI request object
        background_tasks: FastAPI BackgroundTasks for cleanup
        
    Returns:
        EventSourceResponse for SSE streaming
        
    Raises:
        HTTPException: If the project is not found or other errors occur
    """
    try:
        # Initialize agent framework if needed
        agent_framework = get_agent_framework()
        if not agent_framework.is_initialized():
            await agent_framework.initialize()
        
        # Register SSE client
        client_id, sse_response = await agent_sse_manager.register_client(
            request, client_type="assistant"
        )
        
        # Start processing in background
        background_tasks.add_task(
            _process_query_background,
            project_id,
            request_data,
            client_id,
            agent_framework
        )
        
        # Clean up stale connections
        background_tasks.add_task(
            agent_sse_manager.cleanup_completed_requests,
            max_age_seconds=3600
        )
        
        return sse_response
        
    except Exception as e:
        logger.error(f"Error setting up assistant query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process assistant query: {str(e)}"
        )


async def _process_query_background(
    project_id: str,
    request_data: AssistantQueryRequest,
    client_id: str,
    agent_framework
) -> None:
    """Process query in background with SSE streaming."""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Get agent instance
        agent = agent_framework.get_agent()
        
        # Process the query through the agent
        await agent.process_query(
            project_id=project_id,
            user_message=request_data.user_message,
            client_id=client_id,
            routing_override=request_data.routing_override.value if request_data.routing_override else None
        )
        
    except Exception as e:
        logger.error(f"Error in background query processing: {str(e)}")
        
        # Send error event
        await agent_sse_manager.send_error_event(
            client_id=client_id,
            error=str(e),
            trace_id=request_id,
            request_id=request_id
        )


@router.get("/projects/{project_id}/status")
async def get_assistant_status(project_id: str) -> Dict[str, Any]:
    """Get assistant status for a project.
    
    Args:
        project_id: The project ID
        
    Returns:
        Dictionary with assistant status information
    """
    try:
        agent_framework = get_agent_framework()
        
        return {
            "project_id": project_id,
            "framework_status": agent_framework.get_framework_status(),
            "active_connections": agent_sse_manager.get_client_count("assistant"),
            "active_requests": len(agent_sse_manager.request_trackers)
        }
        
    except Exception as e:
        logger.error(f"Error getting assistant status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assistant status: {str(e)}"
        )


@router.get("/framework/status")
async def get_framework_status() -> Dict[str, Any]:
    """Get agent framework status.
    
    Returns:
        Dictionary with framework status information
    """
    try:
        agent_framework = get_agent_framework()
        
        return agent_framework.get_framework_status()
        
    except Exception as e:
        logger.error(f"Error getting framework status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get framework status: {str(e)}"
        )


@router.post("/framework/initialize")
async def initialize_framework() -> Dict[str, Any]:
    """Initialize the agent framework.
    
    Returns:
        Dictionary with initialization result
    """
    try:
        agent_framework = get_agent_framework()
        
        if agent_framework.is_initialized():
            return {
                "success": True,
                "message": "Framework already initialized",
                "status": agent_framework.get_framework_status()
            }
        
        await agent_framework.initialize()
        
        return {
            "success": True,
            "message": "Framework initialized successfully",
            "status": agent_framework.get_framework_status()
        }
        
    except Exception as e:
        logger.error(f"Error initializing framework: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize framework: {str(e)}"
        )


@router.post("/framework/reload")
async def reload_framework_config() -> Dict[str, Any]:
    """Reload framework configuration.
    
    Returns:
        Dictionary with reload result
    """
    try:
        agent_framework = get_agent_framework()
        agent_framework.reload_configuration()
        
        return {
            "success": True,
            "message": "Configuration reloaded successfully",
            "status": agent_framework.get_framework_status()
        }
        
    except Exception as e:
        logger.error(f"Error reloading configuration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reload configuration: {str(e)}"
        )


@router.get("/tools")
async def get_available_tools() -> Dict[str, Any]:
    """Get information about available tools.
    
    Returns:
        Dictionary with tool information
    """
    try:
        agent_framework = get_agent_framework()
        
        if not agent_framework.is_initialized():
            await agent_framework.initialize()
        
        agent = agent_framework.get_agent()
        tool_info = agent.get_tool_info()
        
        return {
            "tools": tool_info,
            "total_tools": len(tool_info)
        }
        
    except Exception as e:
        logger.error(f"Error getting tool information: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tool information: {str(e)}"
        )


@router.get("/metrics/{request_id}")
async def get_request_metrics(request_id: str) -> Dict[str, Any]:
    """Get metrics for a specific request.
    
    Args:
        request_id: The request ID
        
    Returns:
        Dictionary with request metrics
        
    Raises:
        HTTPException: If the request is not found
    """
    try:
        metrics = agent_sse_manager.get_request_metrics(request_id)
        
        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Request {request_id} not found"
            )
        
        return metrics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request metrics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get request metrics: {str(e)}"
        )


@router.delete("/connections")
async def cleanup_connections() -> Dict[str, Any]:
    """Clean up stale SSE connections.
    
    Returns:
        Dictionary with cleanup result
    """
    try:
        # Clean up stale connections
        cleaned_connections = agent_sse_manager.cleanup_stale_connections(max_age_seconds=300)
        
        # Clean up completed requests
        cleaned_requests = agent_sse_manager.cleanup_completed_requests(max_age_seconds=3600)
        
        return {
            "success": True,
            "cleaned_connections": cleaned_connections,
            "cleaned_requests": cleaned_requests,
            "active_connections": agent_sse_manager.get_client_count("assistant"),
            "active_requests": len(agent_sse_manager.request_trackers)
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up connections: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clean up connections: {str(e)}"
        )


# Non-SSE endpoint for testing (optional)
@router.post("/projects/{project_id}/analyze", response_model=AssistantResponse)
async def analyze_project_sync(
    project_id: str,
    request_data: AssistantQueryRequest
) -> AssistantResponse:
    """Synchronous analysis endpoint (for testing purposes).
    
    This endpoint provides synchronous analysis without SSE streaming.
    Mainly used for testing and debugging.
    
    Args:
        project_id: The project ID for context
        request_data: The query request data
        
    Returns:
        AssistantResponse with analysis results
        
    Raises:
        HTTPException: If analysis fails
    """
    try:
        # Initialize agent framework if needed
        agent_framework = get_agent_framework()
        if not agent_framework.is_initialized():
            await agent_framework.initialize()
        
        # Create a mock client ID for synchronous processing
        client_id = f"sync-{uuid.uuid4()}"
        start_time = time.time()
        
        # Process query synchronously (this is a simplified version)
        # In practice, you might want to implement a separate sync method
        agent = agent_framework.get_agent()
        
        # For now, return a placeholder response
        # TODO: Implement actual synchronous processing
        
        execution_time = int((time.time() - start_time) * 1000)
        
        return AssistantResponse(
            success=True,
            data=StructuredAnalysisResponse(
                suggestions=[],
                scores={
                    "integration_consistency": 0.5,
                    "requirements_coverage": 0.5,
                    "security_readiness": 0.5,
                    "operability": 0.5
                },
                status="ok"
            ),
            metadata={
                "execution_time_ms": execution_time,
                "project_id": project_id,
                "sync_mode": True
            }
        )
        
    except Exception as e:
        logger.error(f"Error in synchronous analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}"
        )

# Health Check Endpoints
@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Comprehensive health check for the agent system.
    
    Returns:
        Dictionary with health status information
    """
    try:
        health_result = await health_monitor.check_health(include_details=True)
        
        # Set HTTP status based on health
        if health_result["overall_status"] == "unhealthy":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=health_result
            )
        
        return health_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/liveness")
async def liveness_check() -> Dict[str, Any]:
    """Liveness check - basic system availability.
    
    Returns:
        Dictionary with liveness status
    """
    try:
        liveness_result = await health_monitor.check_liveness()
        
        if not liveness_result["alive"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=liveness_result
            )
        
        return liveness_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liveness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Liveness check failed: {str(e)}"
        )


@router.get("/health/readiness")
async def readiness_check() -> Dict[str, Any]:
    """Readiness check - system ready to serve requests.
    
    Returns:
        Dictionary with readiness status
    """
    try:
        readiness_result = await health_monitor.check_readiness()
        
        if not readiness_result["ready"]:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=readiness_result
            )
        
        return readiness_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/health/history")
async def health_history(limit: int = 10) -> Dict[str, Any]:
    """Get health check history.
    
    Args:
        limit: Maximum number of history entries to return
        
    Returns:
        Dictionary with health history
    """
    try:
        history = health_monitor.get_health_history(limit=limit)
        
        return {
            "history": history,
            "count": len(history)
        }
        
    except Exception as e:
        logger.error(f"Error getting health history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get health history: {str(e)}"
        )