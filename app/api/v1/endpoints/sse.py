"""SSE endpoints.

This module provides endpoints for Server-Sent Events (SSE).
"""
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from app.core.events import SSEManager
from app.api.dependencies import get_sse_manager, get_sse_connection, cleanup_stale_sse_connections
from app.api.schemas import (
    SSEMessageCreate,
    SSEMessageResponse,
    SSEClientsResponse,
    SSEClientDisconnectResponse,
    SSEClientsDisconnectResponse,
    SSEHeartbeatResponse,
)

router = APIRouter(prefix="/sse", tags=["sse"])

@router.get("/connect")
async def connect_sse(
    request: Request,
    client_type: str = "generic",
    background_tasks: BackgroundTasks = None,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> EventSourceResponse:
    """Establish an SSE connection.
    
    This endpoint establishes a Server-Sent Events (SSE) connection
    with the client. The connection will remain open until the client
    disconnects or the server closes the connection.
    
    Args:
        request: The FastAPI request object
        client_type: Type of client for categorization purposes
        background_tasks: FastAPI BackgroundTasks for async cleanup
        sse_manager: The SSE manager instance
        
    Returns:
        An EventSourceResponse that establishes the SSE connection
    """
    # Clean up stale connections
    if background_tasks:
        sse_manager.cleanup_stale_connections(background_tasks)
    
    # Register the client and get the connection
    client_id, response = await sse_manager.register_client(request, client_type)
    
    # Send an initial event to confirm the connection
    await sse_manager.send_event(
        client_id,
        "connected",
        {
            "client_id": client_id,
            "message": "SSE connection established"
        }
    )
    
    return response

@router.post("/broadcast", response_model=SSEMessageResponse)
async def broadcast_event(
    message: SSEMessageCreate,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Dict[str, Any]:
    """Broadcast an event to all connected clients.
    
    This endpoint broadcasts an event to all connected clients
    or to clients of a specific type if specified.
    
    Args:
        message: The message to broadcast
        sse_manager: The SSE manager instance
        
    Returns:
        A dictionary with the number of clients the event was sent to
    """
    sent_count = await sse_manager.broadcast_event(
        message.event_type,
        message.data,
        message.client_type
    )
    
    return {
        "sent_count": sent_count,
        "event_type": message.event_type,
        "data": message.data
    }

@router.post("/send/{client_id}", response_model=SSEClientDisconnectResponse)
async def send_event(
    client_id: str,
    message: SSEMessageCreate,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Dict[str, Any]:
    """Send an event to a specific client.
    
    This endpoint sends an event to a specific client.
    
    Args:
        client_id: The ID of the client to send the event to
        message: The message to send
        sse_manager: The SSE manager instance
        
    Returns:
        A dictionary with the result of the operation
        
    Raises:
        HTTPException: If the client is not found
    """
    success = await sse_manager.send_event(
        client_id,
        message.event_type,
        message.data
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Client with ID {client_id} not found"
        )
    
    return {
        "success": True,
        "client_id": client_id,
        "message": f"Event {message.event_type} sent to client {client_id}"
    }

@router.get("/clients", response_model=SSEClientsResponse)
async def get_clients(
    client_type: Optional[str] = None,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Dict[str, Any]:
    """Get information about connected clients.
    
    This endpoint returns information about connected clients.
    
    Args:
        client_type: If specified, only return clients of this type
        sse_manager: The SSE manager instance
        
    Returns:
        A dictionary with information about connected clients
    """
    return {
        "client_count": sse_manager.get_client_count(client_type),
        "clients": sse_manager.get_client_ids(client_type)
    }

@router.delete("/clients/{client_id}", response_model=SSEClientDisconnectResponse)
async def disconnect_client(
    client_id: str,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Dict[str, Any]:
    """Disconnect a specific client.
    
    This endpoint disconnects a specific client.
    
    Args:
        client_id: The ID of the client to disconnect
        sse_manager: The SSE manager instance
        
    Returns:
        A dictionary with the result of the operation
    """
    await sse_manager.unregister_client(client_id)
    
    return {
        "success": True,
        "client_id": client_id,
        "message": "Client disconnected"
    }

@router.delete("/clients", response_model=SSEClientsDisconnectResponse)
async def disconnect_all_clients(
    client_type: Optional[str] = None,
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Dict[str, Any]:
    """Disconnect all clients.
    
    This endpoint disconnects all clients or clients of a specific type.
    
    Args:
        client_type: If specified, only disconnect clients of this type
        sse_manager: The SSE manager instance
        
    Returns:
        A dictionary with the result of the operation
    """
    if client_type:
        client_ids = sse_manager.get_client_ids(client_type)
        for client_id in client_ids:
            await sse_manager.unregister_client(client_id)
        
        return {
            "success": True,
            "client_count": len(client_ids),
            "client_type": client_type,
            "message": f"Disconnected {len(client_ids)} clients of type {client_type}"
        }
    else:
        client_count = sse_manager.get_client_count()
        await sse_manager.close_all_connections()
        
        return {
            "success": True,
            "client_count": client_count,
            "message": f"Disconnected {client_count} clients"
        }

@router.get("/heartbeat", response_model=SSEHeartbeatResponse)
async def send_heartbeat(
    sse_manager: SSEManager = Depends(get_sse_manager)
) -> Dict[str, Any]:
    """Send a heartbeat event to all clients.
    
    This endpoint sends a heartbeat event to all connected clients.
    
    Args:
        sse_manager: The SSE manager instance
        
    Returns:
        A dictionary with the result of the operation
    """
    await sse_manager.send_heartbeat()
    
    return {
        "success": True,
        "client_count": sse_manager.get_client_count(),
        "message": "Heartbeat sent"
    }