"""Custom JSON encoder for handling datetime and other non-serializable objects."""

import json
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Any


class CustomJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime, date, Decimal, and Enum objects."""
    
    def default(self, obj: Any) -> Any:
        """Convert non-serializable objects to serializable format.
        
        Args:
            obj: The object to serialize.
            
        Returns:
            A JSON-serializable representation of the object.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        elif isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, Enum):
            return obj.value
        elif hasattr(obj, '__dict__'):
            # For custom objects, try to serialize their dict representation
            return obj.__dict__
        
        return super().default(obj)


def json_dumps(obj: Any, **kwargs) -> str:
    """JSON dumps with custom encoder.
    
    Args:
        obj: The object to serialize.
        **kwargs: Additional arguments to pass to json.dumps.
        
    Returns:
        JSON string representation of the object.
    """
    return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)


def safe_json_dumps(obj: Any, **kwargs) -> str:
    """Safe JSON dumps that won't raise serialization errors.
    
    Args:
        obj: The object to serialize.
        **kwargs: Additional arguments to pass to json.dumps.
        
    Returns:
        JSON string representation of the object, or error message if serialization fails.
    """
    try:
        return json_dumps(obj, **kwargs)
    except (TypeError, ValueError) as e:
        # If serialization fails, return a safe error representation
        return json.dumps({
            "error": "Serialization failed",
            "error_type": str(type(e).__name__),
            "error_message": str(e),
            "object_type": str(type(obj).__name__)
        })