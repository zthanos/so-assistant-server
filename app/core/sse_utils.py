"""SSE utility functions.

This module provides utility functions for working with Server-Sent Events (SSE)
in the application, particularly for streaming LLM responses and agent execution.
"""
import logging
from typing import Any, Dict, Optional
import asyncio
from app.core.events import SSEManager
from app.core.exceptions import SSEException, LLMException

logger = logging.getLogger(__name__)

async def stream_llm_response(
    prompt: str,
    client_id: str,
    sse_manager: SSEManager,
    ollama_client,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Stream an LLM response to a client using SSE.
    
    Args:
        prompt: The prompt to send to the LLM
        client_id: The ID of the client to stream the response to
        sse_manager: The SSE manager instance
        ollama_client: The Ollama client instance
        metadata: Optional metadata to include with the events
        
    Raises:
        SSEException: If there's an error with the SSE connection
        LLMException: If there's an error with the LLM
    """
    metadata = metadata or {}
    try:
        # Send initial event
        await sse_manager.send_event(
            client_id, 
            "start", 
            {
                "message": "Starting LLM processing",
                **metadata
            }
        )
        
        # Stream the response
        try:
            async for chunk in ollama_client.generate_stream_raw(prompt):
                await sse_manager.send_event(
                    client_id, 
                    "chunk", 
                    {
                        "content": chunk,
                        **metadata
                    }
                )
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
                
            # Send completion event
            await sse_manager.send_event(
                client_id, 
                "complete", 
                {
                    "message": "LLM processing complete",
                    **metadata
                }
            )
        except Exception as e:
            logger.error(f"Error streaming LLM response: {str(e)}")
            await sse_manager.send_event(
                client_id, 
                "error", 
                {
                    "message": f"LLM error: {str(e)}",
                    **metadata
                }
            )
            raise LLMException(f"Error streaming LLM response: {str(e)}", original_exception=e)
    except Exception as e:
        logger.error(f"Error in SSE streaming: {str(e)}")
        raise SSEException(f"Error in SSE streaming: {str(e)}", original_exception=e)

async def send_progress_update(
    client_id: str,
    sse_manager: SSEManager,
    progress: float,
    status: str,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Send a progress update event to a client.
    
    Args:
        client_id: The ID of the client to send the event to
        sse_manager: The SSE manager instance
        progress: The progress value (0.0 to 1.0)
        status: The status message
        metadata: Optional metadata to include with the event
        
    Raises:
        SSEException: If there's an error with the SSE connection
    """
    metadata = metadata or {}
    try:
        await sse_manager.send_event(
            client_id,
            "progress",
            {
                "progress": progress,
                "status": status,
                **metadata
            }
        )
    except Exception as e:
        logger.error(f"Error sending progress update: {str(e)}")
        raise SSEException(f"Error sending progress update: {str(e)}", original_exception=e)
asy
nc def stream_agent_response(
    project_id: str,
    user_message: str,
    client_id: str,
    sse_manager: SSEManager,
    agent_framework,
    routing_override: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """Stream an agent response to a client using SSE.
    
    Args:
        project_id: The project ID for context
        user_message: The user's query message
        client_id: The ID of the client to stream the response to
        sse_manager: The SSE manager instance
        agent_framework: The agent framework instance
        routing_override: Optional intent override
        metadata: Optional metadata to include with the events
        
    Raises:
        SSEException: If there's an error with the SSE connection
        LLMException: If there's an error with the agent execution
    """
    metadata = metadata or {}
    try:
        # Get the agent instance
        agent = agent_framework.get_agent()
        
        # Process the query through the agent
        await agent.process_query(
            project_id=project_id,
            user_message=user_message,
            client_id=client_id,
            routing_override=routing_override
        )
        
    except Exception as e:
        logger.error(f"Error streaming agent response: {str(e)}")
        await sse_manager.send_event(
            client_id,
            "error",
            {
                "message": f"Agent error: {str(e)}",
                "trace_id": client_id,
                **metadata
            }
        )
        raise LLMException(f"Error streaming agent response: {str(e)}", original_exception=e)

async def send_structured_response(
    client_id: str,
    sse_manager: SSEManager,
    response_data: Dict[str, Any],
    request_id: Optional[str] = None,
    chunk_size: int = 1000
) -> None:
    """Send a structured response in chunks via SSE.
    
    Args:
        client_id: The ID of the client to send the response to
        sse_manager: The SSE manager instance
        response_data: The structured response data
        request_id: Optional request ID for tracking
        chunk_size: Size of JSON chunks to send
        
    Raises:
        SSEException: If there's an error with the SSE connection
    """
    try:
        import json
        
        # Convert to JSON string
        json_str = json.dumps(response_data, indent=2)
        
        # Send in chunks for large responses
        if len(json_str) > chunk_size:
            # Send partial JSON events
            for i in range(0, len(json_str), chunk_size):
                chunk = json_str[i:i + chunk_size]
                await sse_manager.send_event(
                    client_id,
                    "json",
                    {
                        "partial": chunk,
                        "chunk_index": i // chunk_size,
                        "is_final_chunk": i + chunk_size >= len(json_str),
                        "request_id": request_id
                    }
                )
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        # Send final complete response
        await sse_manager.send_event(
            client_id,
            "final",
            {
                "result": response_data,
                "request_id": request_id,
                "timestamp": asyncio.get_event_loop().time()
            }
        )
        
    except Exception as e:
        logger.error(f"Error sending structured response: {str(e)}")
        raise SSEException(f"Error sending structured response: {str(e)}", original_exception=e)