"""LLM schemas.

This module provides Pydantic models for LLM-related data.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class LLMRequestBase(BaseModel):
    """Base model for LLM requests."""
    prompt: str = Field(..., description="The prompt to send to the LLM")
    prompt_key: str = Field("unknown", description="A key for logging and analytics")
    system_prompt: Optional[str] = Field(None, description="Optional system prompt to prepend")
    
class LLMRequest(LLMRequestBase):
    """Model for LLM requests."""
    options: Optional[Dict[str, Any]] = Field(None, description="Optional model parameters")
    
class LLMStreamRequest(LLMRequest):
    """Model for streaming LLM requests."""
    pass
    
class LLMResponseBase(BaseModel):
    """Base model for LLM responses."""
    prompt_key: str = Field(..., description="The prompt key used for the request")
    
class LLMResponse(LLMResponseBase):
    """Model for LLM responses."""
    content: str = Field(..., description="The LLM response content")
    
class LLMStreamResponse(LLMResponseBase):
    """Model for streaming LLM responses."""
    event_type: str = Field(..., description="The type of event")
    data: Dict[str, Any] = Field(..., description="The event data")
    
class LLMErrorResponse(LLMResponseBase):
    """Model for LLM error responses."""
    error: str = Field(..., description="The error message")
    error_type: str = Field(..., description="The type of error")