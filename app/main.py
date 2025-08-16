"""FastAPI application setup."""
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
import logging
import json
from datetime import datetime
from typing import Any

# Import core modules
from app.core.database import init_db, async_init_db
from app.core.exceptions import AppException

# Import all domain models to ensure they are registered with SQLAlchemy
import app.domain.models  # This imports all models

# Import API router
from app.api.v1.router import router as api_v1_router

# Custom JSON encoder for datetime objects
class CustomJSONResponse(JSONResponse):
    """Custom JSON response that handles datetime serialization."""
    
    def render(self, content: Any) -> bytes:
        """Render content to JSON bytes with custom datetime handling."""
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
            default=self._json_encoder
        ).encode("utf-8")
    
    @staticmethod
    def _json_encoder(obj: Any) -> Any:
        """Custom JSON encoder for non-serializable objects."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Startup
    logging.info("Initializing database...")
    try:
        await async_init_db()
    except RuntimeError:
        # Fall back to synchronous initialization if async is not available
        init_db()
    logging.info("Database initialized.")
    yield
    # Shutdown
    logging.info("Shutting down...")

# Create the FastAPI application
app = FastAPI(
    title="Solution Outline Assistant API",
    description="API to help architects create Solution Outlines.",
    version="0.1.0",
    lifespan=lifespan,
    default_response_class=CustomJSONResponse
)

# Add middleware
from app.core.middleware import ErrorLoggingMiddleware, SSEMiddleware

# Add error logging middleware
app.add_middleware(ErrorLoggingMiddleware)

# Add SSE middleware
app.add_middleware(SSEMiddleware)

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, in production use specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
from app.core.exceptions import register_exception_handlers
register_exception_handlers(app)

# Root endpoint
@app.get("/")
def read_root():
    """Root endpoint to check if the API is running."""
    return {"message": "Welcome to the Solution Outline Assistant API!"}

# Include API routers
app.include_router(api_v1_router)