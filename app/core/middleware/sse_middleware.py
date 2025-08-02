"""SSE middleware.

This module provides middleware for handling SSE connections.
"""
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class SSEMiddleware(BaseHTTPMiddleware):
    """Middleware for handling SSE connections.
    
    This middleware adds headers and configuration for SSE connections.
    """
    
    def __init__(self, app: ASGIApp):
        """Initialize the middleware.
        
        Args:
            app: The ASGI application
        """
        super().__init__(app)
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request.
        
        Args:
            request: The request to process
            call_next: The next middleware or route handler
            
        Returns:
            The response
        """
        # Check if this is an SSE request (based on Accept header)
        if request.headers.get("accept") == "text/event-stream":
            logger.debug("SSE connection request detected")
            
            # Call the next middleware or route handler
            response = await call_next(request)
            
            # Add SSE-specific headers if not already present
            if response.headers.get("content-type") != "text/event-stream":
                response.headers["content-type"] = "text/event-stream"
                
            # Ensure caching headers are set correctly for SSE
            response.headers["cache-control"] = "no-cache"
            response.headers["connection"] = "keep-alive"
            
            return response
        
        # Not an SSE request, just pass it through
        return await call_next(request)