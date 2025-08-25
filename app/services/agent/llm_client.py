"""Enhanced Ollama client for LangChain integration."""
import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
import httpx
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.outputs import GenerationChunk

from app.config.config import OLLAMA_HOST, LLM_MODEL, MODEL_CONTEXT_LIMIT
from app.services.agent.config import agent_config
from app.core.exceptions import LLMException

logger = logging.getLogger(__name__)


class StreamingOllamaClient(LLM):
    """Enhanced Ollama client with streaming support for LangChain."""
    
    base_url: str = OLLAMA_HOST
    model_name: str = LLM_MODEL
    temperature: float = agent_config.temperature
    max_tokens: int = agent_config.max_tokens
    timeout: int = agent_config.timeout_seconds
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        """Initialize the streaming Ollama client."""
        # Set defaults if not provided in kwargs
        if "base_url" not in kwargs:
            kwargs["base_url"] = OLLAMA_HOST
        if "model_name" not in kwargs:
            kwargs["model_name"] = LLM_MODEL
        super().__init__(**kwargs)
        
    @property
    def _llm_type(self) -> str:
        """Return identifier of llm type."""
        return "streaming_ollama"
    
    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the Ollama API synchronously."""
        try:
            # Run the async method in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._acall(prompt, stop, run_manager, **kwargs))
            finally:
                loop.close()
        except Exception as e:
            logger.error(f"Error in Ollama _call: {str(e)}")
            raise LLMException(f"Ollama API call failed: {str(e)}")
    
    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """Call the Ollama API asynchronously."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                result = data.get("response", "").strip()
                
                if run_manager:
                    run_manager.on_llm_end({"generations": [[{"text": result}]]})
                
                return result
                
        except httpx.TimeoutException as e:
            logger.error(f"Ollama API timeout: {str(e)}")
            raise LLMException(f"Ollama API timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama API HTTP error: {e.response.status_code} - {e.response.text}")
            raise LLMException(f"Ollama API error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama _acall: {str(e)}")
            raise LLMException(f"Ollama API call failed: {str(e)}")
    
    async def _astream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[GenerationChunk, None]:
        """Stream the Ollama API response asynchronously."""
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": True,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                }
            }
            
            if stop:
                payload["options"]["stop"] = stop
                
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    chunk_text = data["response"]
                                    if chunk_text:
                                        chunk = GenerationChunk(text=chunk_text)
                                        if run_manager:
                                            run_manager.on_llm_new_token(chunk_text, chunk=chunk)
                                        yield chunk
                                        
                                if data.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse streaming response: {line}")
                                continue
                                
        except httpx.TimeoutException as e:
            logger.error(f"Ollama streaming timeout: {str(e)}")
            raise LLMException(f"Ollama streaming timeout after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"Ollama streaming HTTP error: {e.response.status_code}")
            raise LLMException(f"Ollama streaming error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Unexpected error in Ollama streaming: {str(e)}")
            raise LLMException(f"Ollama streaming failed: {str(e)}")
    
    async def generate_stream(self, prompt: str, prompt_key: str = "unknown") -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM (convenience method)."""
        logger.debug(f"Starting streaming generation for prompt_key: {prompt_key}")
        
        try:
            async for chunk in self._astream(prompt):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"Error in generate_stream: {str(e)}")
            raise
    
    async def generate(self, prompt: str, prompt_key: str = "unknown") -> str:
        """Generate a complete response from the LLM (convenience method)."""
        logger.debug(f"Starting generation for prompt_key: {prompt_key}")
        
        try:
            return await self._acall(prompt)
        except Exception as e:
            logger.error(f"Error in generate: {str(e)}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text (rough approximation)."""
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def check_context_limit(self, text: str) -> Dict[str, Any]:
        """Check if text fits within context limits."""
        estimated_tokens = self.estimate_tokens(text)
        return {
            "estimated_tokens": estimated_tokens,
            "context_limit": MODEL_CONTEXT_LIMIT,
            "fits": estimated_tokens <= MODEL_CONTEXT_LIMIT,
            "utilization": estimated_tokens / MODEL_CONTEXT_LIMIT
        }


# Global streaming client instance
streaming_ollama_client = StreamingOllamaClient()