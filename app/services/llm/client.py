"""Enhanced Ollama client with streaming support.

This module provides an enhanced Ollama client that supports streaming responses
from the LLM. It builds on the existing Ollama client functionality but adds
support for streaming responses using async generators.
"""
import httpx
import asyncio
import json
from typing import AsyncGenerator, Dict, Any, Optional
import logging

from app.logger import get_logger
from app.prompt_analytics import (
    check_prompt_fits,
    log_prompt_run
)
from app.config.config import OLLAMA_HOST, LLM_MODEL, CALC_MODEL, MODEL_CONTEXT_LIMIT
from app.core.exceptions import LLMException

logger = get_logger()

class StreamingOllamaClient:
    """Enhanced Ollama client with streaming support.
    
    This class provides methods for generating responses from the Ollama LLM,
    with support for both streaming and non-streaming responses.
    """
    
    def __init__(
        self,
        host: str = OLLAMA_HOST,
        model: str = LLM_MODEL,
        context_limit: int = MODEL_CONTEXT_LIMIT
    ):
        """Initialize the client.
        
        Args:
            host: The Ollama host URL
            model: The LLM model to use
            context_limit: The context window limit for the model
        """
        self.host = host
        self.model = model
        self.context_limit = context_limit
        self.logger = logger
        
    async def generate_stream(
        self,
        prompt: str,
        prompt_key: str = "unknown",
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM in SSE format.
        
        This method sends a prompt to the Ollama LLM and yields SSE-formatted
        events with chunks of the response as they become available.
        
        Args:
            prompt: The prompt to send to the LLM
            prompt_key: A key for logging and analytics
            system_prompt: Optional system prompt to prepend
            options: Optional model parameters
            
        Yields:
            SSE-formatted events with LLM response chunks
            Format: "event: llm.chunk\ndata: {\"content\": \"chunk\", \"prompt_key\": \"key\"}\n\n"
            
        Raises:
            LLMException: If there's an error calling the LLM
        """
        # Check token size and cost estimate before sending
        stats = check_prompt_fits(prompt, model_context_limit=self.context_limit)
        prompt_tokens = stats["prompt_tokens"]

        if stats["total_tokens"] > self.context_limit:
            self.logger.warning(
                f"⚠️ Estimated total tokens {stats['total_tokens']} exceed context window ({self.context_limit})."
            )

        url = f"{self.host}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": True
        }
        
        # Add system prompt if provided
        if system_prompt:
            payload["system"] = system_prompt
            
        # Add options if provided
        if options:
            payload.update(options)

        try:
            async with httpx.AsyncClient(timeout=2000.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    
                    # Track the full response for logging
                    full_response = ""
                    
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue
                            
                        try:
                            data = json.loads(line)
                            chunk = data.get("response", "")
                            
                            if chunk:
                                full_response += chunk
                                # Format as SSE event
                                sse_data = {
                                    "content": chunk,
                                    "prompt_key": prompt_key
                                }
                                sse_event = f"event: llm.chunk\ndata: {json.dumps(sse_data)}\n\n"
                                yield sse_event
                                
                            # Check if this is the final response
                            if data.get("done", False):
                                # Send completion event
                                completion_data = {
                                    "content": "",
                                    "prompt_key": prompt_key,
                                    "done": True
                                }
                                completion_event = f"event: llm.complete\ndata: {json.dumps(completion_data)}\n\n"
                                yield completion_event
                                break
                        except json.JSONDecodeError:
                            self.logger.error(f"Failed to parse JSON from Ollama: {line}")
                            continue
                    
                    # Log prompt run to CSV analytics
                    log_prompt_run(
                        prompt_key=prompt_key,
                        model_name=CALC_MODEL,
                        prompt_text=prompt,
                        measured_response_tokens=None  # Could calculate this if needed
                    )
                    
                    self.logger.debug(f"LLM Response (streaming): {full_response[:100]}...")

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP error calling Ollama: {e.response.status_code} - {e.response.text}"
            self.logger.error(f"❌ {error_msg}")
            # Send error event
            error_data = {
                "content": "",
                "prompt_key": prompt_key,
                "error": error_msg
            }
            error_event = f"event: llm.error\ndata: {json.dumps(error_data)}\n\n"
            yield error_event
            raise LLMException(error_msg, original_exception=e)
        except httpx.RequestError as e:
            error_msg = f"Request error calling Ollama: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            # Send error event
            error_data = {
                "content": "",
                "prompt_key": prompt_key,
                "error": error_msg
            }
            error_event = f"event: llm.error\ndata: {json.dumps(error_data)}\n\n"
            yield error_event
            raise LLMException(error_msg, original_exception=e)
        except Exception as e:
            error_msg = f"Error calling Ollama: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            # Send error event
            error_data = {
                "content": "",
                "prompt_key": prompt_key,
                "error": error_msg
            }
            error_event = f"event: llm.error\ndata: {json.dumps(error_data)}\n\n"
            yield error_event
            raise LLMException(error_msg, original_exception=e)
            
    async def generate(
        self,
        prompt: str,
        prompt_key: str = "unknown",
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a complete response from the LLM (non-streaming).
        
        This method sends a prompt to the Ollama LLM and returns the complete
        response. It uses the streaming API internally but collects all chunks
        into a single response by parsing the SSE events.
        
        Args:
            prompt: The prompt to send to the LLM
            prompt_key: A key for logging and analytics
            system_prompt: Optional system prompt to prepend
            options: Optional model parameters
            
        Returns:
            The complete LLM response
            
        Raises:
            LLMException: If there's an error calling the LLM
        """
        result = ""
        try:
            async for sse_event in self.generate_stream(prompt, prompt_key, system_prompt, options):
                # Parse SSE event to extract content
                if "event: llm.chunk" in sse_event:
                    # Extract data line from SSE event
                    lines = sse_event.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data_json = line[6:]  # Remove 'data: ' prefix
                                data = json.loads(data_json)
                                content = data.get("content", "")
                                if content:
                                    result += content
                            except json.JSONDecodeError:
                                continue
                elif "event: llm.complete" in sse_event:
                    # Stream is complete
                    break
                elif "event: llm.error" in sse_event:
                    # Extract error from SSE event
                    lines = sse_event.strip().split('\n')
                    for line in lines:
                        if line.startswith('data: '):
                            try:
                                data_json = line[6:]  # Remove 'data: ' prefix
                                data = json.loads(data_json)
                                error_msg = data.get("error", "Unknown error")
                                raise LLMException(f"LLM error: {error_msg}")
                            except json.JSONDecodeError:
                                continue
            return result
        except Exception as e:
            raise LLMException(f"Error generating non-streaming response: {str(e)}", original_exception=e)
    
    async def generate_stream_raw(
        self,
        prompt: str,
        prompt_key: str = "unknown",
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM (raw content only).
        
        This method provides backward compatibility by yielding just the content
        chunks without SSE formatting.
        
        Args:
            prompt: The prompt to send to the LLM
            prompt_key: A key for logging and analytics
            system_prompt: Optional system prompt to prepend
            options: Optional model parameters
            
        Yields:
            Raw content chunks from the LLM response
            
        Raises:
            LLMException: If there's an error calling the LLM
        """
        async for sse_event in self.generate_stream(prompt, prompt_key, system_prompt, options):
            # Parse SSE event to extract content
            if "event: llm.chunk" in sse_event:
                # Extract data line from SSE event
                lines = sse_event.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        try:
                            data_json = line[6:]  # Remove 'data: ' prefix
                            data = json.loads(data_json)
                            content = data.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
            elif "event: llm.complete" in sse_event:
                # Stream is complete
                break
            elif "event: llm.error" in sse_event:
                # Extract error from SSE event
                lines = sse_event.strip().split('\n')
                for line in lines:
                    if line.startswith('data: '):
                        try:
                            data_json = line[6:]  # Remove 'data: ' prefix
                            data = json.loads(data_json)
                            error_msg = data.get("error", "Unknown error")
                            raise LLMException(f"LLM error: {error_msg}")
                        except json.JSONDecodeError:
                            continue

# Legacy function for backward compatibility
async def async_call_ollama(prompt, prompt_key="unknown"):
    """Legacy async function for backward compatibility.
    
    This function provides backward compatibility with the original
    call_ollama function but in an async context.
    
    Args:
        prompt: The prompt to send to the LLM
        prompt_key: A key for logging and analytics
        
    Returns:
        The complete LLM response
        
    Raises:
        LLMException: If there's an error calling the LLM
    """
    client = StreamingOllamaClient()
    return await client.generate(prompt, prompt_key)