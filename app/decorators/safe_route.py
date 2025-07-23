import functools
from functools import wraps
import logging
from fastapi import HTTPException
from sqlalchemy import true
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse
import json
from typing import Any
from inspect import iscoroutinefunction
logger = logging.getLogger(__name__)


def safe_route(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPException as e:
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error: {e}")
            raise HTTPException(status_code=500, detail="Database error")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

    return wrapper


def safe_get_route(func):
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        try:
            response = await func(*args, **kwargs)  # Προσθήκη await
            if response is None:
                raise HTTPException(404, detail="Resource not found")
            return JSONResponse(response) if _is_json(response) else response
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in GET: {e}")
            raise HTTPException(503, detail="Service temporarily unavailable")
        except Exception as e:
            logger.error(f"Unexpected GET error: {e}")
            raise HTTPException(500, detail="Internal server error")

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            response = func(*args, **kwargs)
            if response is None:
                raise HTTPException(404, detail="Resource not found")
            return JSONResponse(response) if _is_json(response) else response
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Database error in GET: {e}")
            raise HTTPException(503, detail="Service temporarily unavailable")
        except Exception as e:
            logger.error(f"Unexpected GET error: {e}")
            raise HTTPException(500, detail="Internal server error")

    return async_wrapper if iscoroutinefunction(func) else sync_wrapper

def validate_user_access(func):
    @wraps(func)
    async def wrapper(project_id: str, *args, **kwargs):
        if not user_has_access_to_project(project_id):
            raise HTTPException(403, detail="Access denied")
        return await func(project_id, *args, **kwargs)

    return wrapper


def user_has_access_to_project():
    return true


def _is_json(data: Any) -> bool:
    """
    Check if data can be serialized to JSON.
    Returns True for:
    - dict/list (JSON objects/arrays)
    - Basic types (str, int, float, bool, None)
    - Pydantic models (through .dict() or .json())
    Returns False for:
    - SQLAlchemy models
    - Binary data
    - Other non-JSON-serializable types
    """
    try:
        if hasattr(data, "dict"):  # Handle Pydantic models
            data = data.dict()
        elif hasattr(data, "json"):  # Alternative Pydantic serialization
            data = json.loads(data.json())

        json.dumps(data)
        return True
    except (TypeError, ValueError):
        return False
