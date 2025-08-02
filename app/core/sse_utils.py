"""SSE utility functions.

This module provides utility functions for working with Server-Sent Events (SSE)
in the application, particularly for streaming LLM responses.
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
            async for chunk in ollama_client.generate_stream(prompt):
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