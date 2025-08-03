"""LLM endpoints.

This module provides endpoints for interacting with LLMs, including
streaming responses using SSE.
"""
import json
from typing import Dict, Any, Optional, Tuple
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.core.events import SSEManager
from app.services.llm import StreamingOllamaClient, LLMStreamingService
from app.api.dependencies import (
    get_sse_manager,
    get_sse_connection,
    get_llm_streaming_service,
    get_ollama_client,
    cleanup_stale_sse_connections
)
from app.api.schemas import (
    LLMRequest,
    LLMStreamRequest,
    LLMResponse,
    LLMStreamResponse,
    LLMErrorResponse
)
from app.core.exceptions import LLMException, SSEException

router = APIRouter(prefix="/llm", tags=["llm"])

@router.post("/generate", response_model=LLMResponse)
async def generate_llm_response(
    request: LLMRequest,
    ollama_client: StreamingOllamaClient = Depends(get_ollama_client)
) -> Dict[str, Any]:
    """Generate a complete response from the LLM (non-streaming).
    
    This endpoint sends a prompt to the LLM and returns the complete response.
    
    Args:
        request: The LLM request
        ollama_client: The Ollama client instance
        
    Returns:
        A dictionary with the LLM response
        
    Raises:
        HTTPException: If there's an error with the LLM
    """
    try:
        content = await ollama_client.generate(
            request.prompt,
            request.prompt_key,
            request.system_prompt,
            request.options
        )
        
        return {
            "content": content,
            "prompt_key": request.prompt_key
        }
    except LLMException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/stream/connect")
async def connect_llm_stream(
    request: Request,
    background_tasks: BackgroundTasks = None,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> EventSourceResponse:
    """Establish an SSE connection for LLM streaming.
    
    This endpoint establishes a Server-Sent Events (SSE) connection
    for streaming LLM responses.
    
    Args:
        request: The FastAPI request object
        background_tasks: FastAPI BackgroundTasks for async cleanup
        sse_manager: The SSE manager instance
        
    Returns:
        An EventSourceResponse that establishes the SSE connection
    """
    # Clean up stale connections
    if background_tasks:
        sse_manager.cleanup_stale_connections(background_tasks)
    
    # Register the client and get the connection
    client_id, response = await sse_manager.register_client(request, "llm_stream")
    
    # Send an initial event to confirm the connection
    await sse_manager.send_event(
        client_id,
        "connected",
        {
            "client_id": client_id,
            "message": "LLM streaming connection established"
        }
    )
    
    return response

@router.post("/stream/{client_id}")
async def stream_llm_response(
    client_id: str,
    request: LLMStreamRequest,
    background_tasks: BackgroundTasks,
    llm_streaming_service: LLMStreamingService = Depends(get_llm_streaming_service)
) -> Dict[str, Any]:
    """Stream an LLM response to a client using SSE.
    
    This endpoint streams an LLM response to a client using SSE.
    The client must have established an SSE connection using the
    /llm/stream/connect endpoint.
    
    Args:
        client_id: The ID of the client to stream to
        request: The LLM request
        background_tasks: FastAPI BackgroundTasks for async processing
        llm_streaming_service: The LLM streaming service instance
        
    Returns:
        A dictionary with the status of the streaming operation
        
    Raises:
        HTTPException: If there's an error with the LLM or SSE connection
    """
    try:
        # Start streaming in the background
        background_tasks.add_task(
            llm_streaming_service.stream_llm_response,
            client_id,
            request.prompt,
            request.prompt_key,
            request.system_prompt,
            request.options,
            background_tasks
        )
        
        return {
            "status": "streaming",
            "client_id": client_id,
            "prompt_key": request.prompt_key,
            "message": "Streaming started"
        }
    except SSEException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"SSE error: {str(e)}"
        )
    except LLMException as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )

@router.post("/stream", response_class=EventSourceResponse)
async def stream_llm_response_direct(
    request: LLMStreamRequest,
    req: Request,
    ollama_client: StreamingOllamaClient = Depends(get_ollama_client)
) -> EventSourceResponse:
    """Stream an LLM response directly using SSE.
    
    This endpoint streams an LLM response directly using SSE,
    without requiring a separate connection establishment step.
    
    Args:
        request: The LLM request
        req: The FastAPI request object
        ollama_client: The Ollama client instance
        
    Returns:
        An EventSourceResponse that streams the LLM response
    """
    async def event_generator():
        try:
            # Send start event
            yield {
                "event": "llm.start",
                "data": json.dumps({
                    "message": "Starting LLM processing",
                    "prompt_key": request.prompt_key
                })
            }
            
            # Stream the response using raw content chunks
            async for chunk in ollama_client.generate_stream_raw(
                request.prompt,
                request.prompt_key,
                request.system_prompt,
                request.options
            ):
                if await req.is_disconnected():
                    break
                    
                yield {
                    "event": "llm.chunk",
                    "data": json.dumps({
                        "content": chunk,
                        "prompt_key": request.prompt_key
                    })
                }
                
            # Send completion event
            yield {
                "event": "llm.complete",
                "data": json.dumps({
                    "message": "LLM processing complete",
                    "prompt_key": request.prompt_key
                })
            }
        except LLMException as e:
            # Send error event
            yield {
                "event": "llm.error",
                "data": json.dumps({
                    "message": str(e),
                    "prompt_key": request.prompt_key,
                    "error_type": "llm_error"
                })
            }
        except Exception as e:
            # Send error event
            yield {
                "event": "llm.error",
                "data": json.dumps({
                    "message": "An unexpected error occurred",
                    "prompt_key": request.prompt_key,
                    "error_type": "unexpected_error"
                })
            }
    
    return EventSourceResponse(event_generator())