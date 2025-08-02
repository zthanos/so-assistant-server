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
        """Generate a streaming response from the LLM.
        
        This method sends a prompt to the Ollama LLM and yields chunks of the
        response as they become available.
        
        Args:
            prompt: The prompt to send to the LLM
            prompt_key: A key for logging and analytics
            system_prompt: Optional system prompt to prepend
            options: Optional model parameters
            
        Yields:
            Chunks of the LLM response as they become available
            
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
                                yield chunk
                                
                            # Check if this is the final response
                            if data.get("done", False):
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
            raise LLMException(error_msg, original_exception=e)
        except httpx.RequestError as e:
            error_msg = f"Request error calling Ollama: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
            raise LLMException(error_msg, original_exception=e)
        except Exception as e:
            error_msg = f"Error calling Ollama: {str(e)}"
            self.logger.error(f"❌ {error_msg}")
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
        into a single response.
        
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
            async for chunk in self.generate_stream(prompt, prompt_key, system_prompt, options):
                result += chunk
            return result
        except Exception as e:
            raise LLMException(f"Error generating non-streaming response: {str(e)}", original_exception=e)

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