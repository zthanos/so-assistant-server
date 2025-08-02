"""Error handling middleware.

This module provides middleware for handling errors in a consistent way across the application.
"""
import logging
import time
import traceback
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.exceptions import AppException
from app.api.schemas.common import create_error_response
from app.core.json_encoder import safe_json_dumps

logger = logging.getLogger(__name__)

class ErrorLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging errors.
    
    This middleware logs all errors that occur during request processing.
    It also adds request timing information to the logs.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log any errors.
        
        Args:
            request: The incoming request.
            call_next: The next middleware or route handler.
            
        Returns:
            The response from the next middleware or route handler.
        """
        start_time = time.time()
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log slow requests
            if process_time > 1.0:  # Log requests that take more than 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.url.path} took {process_time:.2f}s"
                )
                
            return response
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log the error
            logger.error(
                f"Error during request: {request.method} {request.url.path} took {process_time:.2f}s",
                exc_info=True
            )
            
            # If it's an AppException, let the exception handler handle it
            if isinstance(e, AppException):
                raise
                
            # For other exceptions, return a generic error response using standardized format
            error_response = create_error_response(
                message="Internal server error",
                error_code="INTERNAL_SERVER_ERROR",
                details={
                    "path": request.url.path,
                    "method": request.method,
                    "process_time": f"{process_time:.2f}s"
                }
            )
            
            # Use safe JSON serialization to avoid datetime serialization issues
            try:
                content = error_response.model_dump()
            except Exception:
                # Fallback to a simple error message if model serialization fails
                content = {
                    "success": False,
                    "message": "Internal server error",
                    "error_code": "INTERNAL_SERVER_ERROR"
                }
            
            return JSONResponse(
                status_code=500,
                content=content
            )