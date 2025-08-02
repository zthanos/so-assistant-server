"""Event handling (SSE).

This module provides functionality for Server-Sent Events (SSE) in the application.
It includes a manager class for handling SSE connections, sending events to clients,
and managing the lifecycle of SSE connections.
"""
from fastapi import Request, BackgroundTasks
import asyncio
import uuid
import logging
import time
from typing import Dict, Any, AsyncGenerator, Optional, List
from sse_starlette.sse import EventSourceResponse
from app.core.exceptions import SSEException

logger = logging.getLogger(__name__)

class SSEManager:
    """Server-Sent Events manager.
    
    This class manages SSE connections, including client registration,
    event broadcasting, and connection cleanup.
    """
    
    def __init__(self, connection_timeout: int = 3600):
        """Initialize the SSE manager.
        
        Args:
            connection_timeout: Maximum time in seconds to keep a connection open
        """
        self.clients: Dict[str, asyncio.Queue] = {}
        self.client_info: Dict[str, Dict[str, Any]] = {}
        self.connection_timeout = connection_timeout
        
    async def register_client(self, request: Request, client_type: str = "generic") -> tuple[str, EventSourceResponse]:
        """Register a new client and return the client ID and EventSourceResponse.
        
        Args:
            request: The FastAPI request object
            client_type: Type of client for categorization purposes
            
        Returns:
            A tuple containing the client ID and the EventSourceResponse
            
        Raises:
            SSEException: If there's an error registering the client
        """
        try:
            client_id = str(uuid.uuid4())
            queue = asyncio.Queue()
            self.clients[client_id] = queue
            self.client_info[client_id] = {
                "type": client_type,
                "connected_at": time.time(),
                "last_activity": time.time(),
                "user_agent": request.headers.get("user-agent", "Unknown"),
                "remote_addr": request.client.host if request.client else "Unknown"
            }
            
            logger.info(f"Client {client_id} registered ({client_type})")
            
            async def event_generator():
                try:
                    while True:
                        if await request.is_disconnected():
                            logger.info(f"Client {client_id} disconnected")
                            break
                        
                        # Check for connection timeout
                        if time.time() - self.client_info[client_id]["last_activity"] > self.connection_timeout:
                            logger.info(f"Client {client_id} connection timed out")
                            break
                        
                        try:
                            event = await asyncio.wait_for(queue.get(), timeout=30)  # 30-second keepalive
                            if event is None:  # None is our signal to close the connection
                                break
                                
                            # Update last activity time
                            self.client_info[client_id]["last_activity"] = time.time()
                            
                            yield event
                        except asyncio.TimeoutError:
                            # Send keepalive event
                            yield {"event": "keepalive", "data": ""}
                except Exception as e:
                    logger.error(f"Error in event generator for client {client_id}: {str(e)}")
                    yield {"event": "error", "data": {"message": "Internal server error"}}
                finally:
                    await self.unregister_client(client_id)
                    
            return client_id, EventSourceResponse(event_generator())
        except Exception as e:
            logger.error(f"Error registering client: {str(e)}")
            raise SSEException(f"Failed to register SSE client: {str(e)}")
        
    async def unregister_client(self, client_id: str) -> None:
        """Unregister a client.
        
        Args:
            client_id: The ID of the client to unregister
        """
        if client_id in self.clients:
            try:
                await self.clients[client_id].put(None)  # Signal to close
            except Exception as e:
                logger.error(f"Error sending close signal to client {client_id}: {str(e)}")
            
            del self.clients[client_id]
            if client_id in self.client_info:
                del self.client_info[client_id]
                
            logger.info(f"Client {client_id} unregistered")
            
    async def send_event(self, client_id: str, event_type: str, data: Any) -> bool:
        """Send an event to a specific client.
        
        Args:
            client_id: The ID of the client to send the event to
            event_type: The type of event to send
            data: The data to send with the event
            
        Returns:
            True if the event was sent successfully, False otherwise
        """
        if client_id in self.clients:
            try:
                await self.clients[client_id].put({
                    "event": event_type,
                    "data": data
                })
                # Update last activity time
                if client_id in self.client_info:
                    self.client_info[client_id]["last_activity"] = time.time()
                return True
            except Exception as e:
                logger.error(f"Error sending event to client {client_id}: {str(e)}")
                return False
        return False
            
    async def broadcast_event(self, event_type: str, data: Any, client_type: Optional[str] = None) -> int:
        """Broadcast an event to all connected clients.
        
        Args:
            event_type: The type of event to send
            data: The data to send with the event
            client_type: If specified, only send to clients of this type
            
        Returns:
            The number of clients the event was sent to
        """
        sent_count = 0
        for client_id in list(self.clients.keys()):
            # If client_type is specified, only send to clients of that type
            if client_type and client_id in self.client_info and self.client_info[client_id]["type"] != client_type:
                continue
                
            if await self.send_event(client_id, event_type, data):
                sent_count += 1
        
        return sent_count
        
    def get_client_count(self, client_type: Optional[str] = None) -> int:
        """Get the number of connected clients.
        
        Args:
            client_type: If specified, only count clients of this type
            
        Returns:
            The number of connected clients
        """
        if client_type:
            return sum(1 for cid in self.client_info if self.client_info[cid]["type"] == client_type)
        return len(self.clients)
        
    def get_client_ids(self, client_type: Optional[str] = None) -> List[str]:
        """Get the IDs of connected clients.
        
        Args:
            client_type: If specified, only return clients of this type
            
        Returns:
            A list of client IDs
        """
        if client_type:
            return [cid for cid in self.client_info if self.client_info[cid]["type"] == client_type]
        return list(self.clients.keys())
        
    async def close_all_connections(self) -> None:
        """Close all active SSE connections."""
        for client_id in list(self.clients.keys()):
            await self.unregister_client(client_id)
            
    async def send_heartbeat(self) -> None:
        """Send a heartbeat event to all clients to keep connections alive."""
        await self.broadcast_event("heartbeat", {"timestamp": time.time()})
        
    def cleanup_stale_connections(self, background_tasks: BackgroundTasks) -> int:
        """Clean up stale connections.
        
        Args:
            background_tasks: FastAPI BackgroundTasks for async cleanup
            
        Returns:
            The number of connections that were cleaned up
        """
        now = time.time()
        stale_clients = [
            cid for cid in list(self.client_info.keys())
            if now - self.client_info[cid]["last_activity"] > self.connection_timeout
        ]
        
        for client_id in stale_clients:
            background_tasks.add_task(self.unregister_client, client_id)
            
        if stale_clients:
            logger.info(f"Cleaned up {len(stale_clients)} stale connections")
            
        return len(stale_clients)