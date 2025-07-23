import json
from typing import Any

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
