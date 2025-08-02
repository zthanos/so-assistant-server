"""SSE schemas.

This module provides Pydantic models for SSE-related data.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class SSEMessageBase(BaseModel):
    """Base model for SSE messages."""
    event_type: str = Field(..., description="Type of the event")
    data: Dict[str, Any] = Field(..., description="Data payload of the event")

class SSEMessageCreate(SSEMessageBase):
    """Model for creating an SSE message."""
    client_id: Optional[str] = Field(None, description="ID of the client to send the event to")
    client_type: Optional[str] = Field(None, description="Type of clients to send the event to")

class SSEMessageResponse(SSEMessageBase):
    """Model for SSE message response."""
    sent_count: int = Field(..., description="Number of clients the event was sent to")

class SSEClientInfo(BaseModel):
    """Model for SSE client information."""
    client_id: str = Field(..., description="ID of the client")
    client_type: str = Field(..., description="Type of the client")
    connected_at: float = Field(..., description="Timestamp when the client connected")
    last_activity: float = Field(..., description="Timestamp of the last activity")
    user_agent: str = Field(..., description="User agent of the client")
    remote_addr: str = Field(..., description="Remote address of the client")

class SSEClientsResponse(BaseModel):
    """Model for SSE clients response."""
    client_count: int = Field(..., description="Number of connected clients")
    clients: List[str] = Field(..., description="List of client IDs")

class SSEClientDisconnectResponse(BaseModel):
    """Model for SSE client disconnect response."""
    success: bool = Field(..., description="Whether the operation was successful")
    client_id: str = Field(..., description="ID of the disconnected client")
    message: str = Field(..., description="Message about the operation")

class SSEClientsDisconnectResponse(BaseModel):
    """Model for SSE clients disconnect response."""
    success: bool = Field(..., description="Whether the operation was successful")
    client_count: int = Field(..., description="Number of disconnected clients")
    client_type: Optional[str] = Field(None, description="Type of disconnected clients")
    message: str = Field(..., description="Message about the operation")

class SSEHeartbeatResponse(BaseModel):
    """Model for SSE heartbeat response."""
    success: bool = Field(..., description="Whether the operation was successful")
    client_count: int = Field(..., description="Number of connected clients")
    message: str = Field(..., description="Message about the operation")