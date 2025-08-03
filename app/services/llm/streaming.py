"""LLM streaming service.

This module provides a service for streaming LLM responses using SSE.
It connects the enhanced Ollama client with the SSE manager to stream
responses in real-time.
"""
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, Tuple
from fastapi import BackgroundTasks

from app.core.events import SSEManager
from app.services.llm.client import StreamingOllamaClient
from app.core.exceptions import LLMException, SSEException

logger = logging.getLogger(__name__)

class LLMStreamingService:
    """Service for streaming LLM responses.
    
    This class provides methods for streaming LLM responses using SSE.
    It connects the enhanced Ollama client with the SSE manager to stream
    responses in real-time.
    """
    
    def __init__(
        self,
        sse_manager: SSEManager,
        ollama_client: Optional[StreamingOllamaClient] = None
    ):
        """Initialize the service.
        
        Args:
            sse_manager: The SSE manager instance
            ollama_client: Optional Ollama client instance (created if not provided)
        """
        self.sse_manager = sse_manager
        self.ollama_client = ollama_client or StreamingOllamaClient()
        
    async def stream_llm_response(
        self,
        client_id: str,
        prompt: str,
        prompt_key: str = "unknown",
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        background_tasks: Optional[BackgroundTasks] = None
    ) -> None:
        """Stream an LLM response to a client using SSE.
        
        This method streams an LLM response to a client using SSE. It sends
        events for the start, chunks, completion, and any errors.
        
        Args:
            client_id: The ID of the client to stream to
            prompt: The prompt to send to the LLM
            prompt_key: A key for logging and analytics
            system_prompt: Optional system prompt to prepend
            options: Optional model parameters
            background_tasks: Optional background tasks for cleanup
            
        Raises:
            SSEException: If there's an error with the SSE connection
            LLMException: If there's an error with the LLM
        """
        try:
            # Send initial event
            await self.sse_manager.send_event(
                client_id,
                "llm.start",
                {
                    "message": "Starting LLM processing",
                    "prompt_key": prompt_key
                }
            )
            
            # Stream the response
            try:
                async for chunk in self.ollama_client.generate_stream_raw(
                    prompt,
                    prompt_key,
                    system_prompt,
                    options
                ):
                    await self.sse_manager.send_event(
                        client_id,
                        "llm.chunk",
                        {
                            "content": chunk,
                            "prompt_key": prompt_key
                        }
                    )
                    
                # Send completion event
                await self.sse_manager.send_event(
                    client_id,
                    "llm.complete",
                    {
                        "message": "LLM processing complete",
                        "prompt_key": prompt_key
                    }
                )
            except LLMException as e:
                # Send error event
                await self.sse_manager.send_event(
                    client_id,
                    "llm.error",
                    {
                        "message": str(e),
                        "prompt_key": prompt_key,
                        "error_type": "llm_error"
                    }
                )
                # Re-raise the exception for proper handling
                raise
                
        except SSEException as e:
            logger.error(f"SSE error while streaming LLM response: {str(e)}")
            # We can't send an event if there's an SSE error, so just log it
            raise
        except Exception as e:
            logger.error(f"Unexpected error while streaming LLM response: {str(e)}")
            # Try to send an error event, but don't raise if it fails
            try:
                await self.sse_manager.send_event(
                    client_id,
                    "llm.error",
                    {
                        "message": "An unexpected error occurred",
                        "prompt_key": prompt_key,
                        "error_type": "unexpected_error"
                    }
                )
            except Exception:
                pass
            # Re-raise the original exception
            raise
            
    async def create_streaming_response(
        self,
        prompt: str,
        prompt_key: str = "unknown",
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Tuple[str, Dict[str, Any]], None]:
        """Create a streaming response without using SSE.
        
        This method creates a streaming response without using SSE. It's useful
        for cases where you want to stream the response but don't want to use SSE.
        
        Args:
            prompt: The prompt to send to the LLM
            prompt_key: A key for logging and analytics
            system_prompt: Optional system prompt to prepend
            options: Optional model parameters
            
        Yields:
            Tuples of (event_type, data) for each chunk of the response
            
        Raises:
            LLMException: If there's an error with the LLM
        """
        try:
            # Yield start event
            yield ("llm.start", {
                "message": "Starting LLM processing",
                "prompt_key": prompt_key
            })
            
            # Stream the response
            async for chunk in self.ollama_client.generate_stream_raw(
                prompt,
                prompt_key,
                system_prompt,
                options
            ):
                yield ("llm.chunk", {
                    "content": chunk,
                    "prompt_key": prompt_key
                })
                
            # Yield completion event
            yield ("llm.complete", {
                "message": "LLM processing complete",
                "prompt_key": prompt_key
            })
                
        except LLMException as e:
            # Yield error event
            yield ("llm.error", {
                "message": str(e),
                "prompt_key": prompt_key,
                "error_type": "llm_error"
            })
            # Re-raise the exception for proper handling
            raise
        except Exception as e:
            # Yield error event
            yield ("llm.error", {
                "message": "An unexpected error occurred",
                "prompt_key": prompt_key,
                "error_type": "unexpected_error"
            })
            # Re-raise the exception for proper handling
            raise