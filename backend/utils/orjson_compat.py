"""
backend/utils/orjson_compat.py — High-performance JSON serializer bindings utilizing orjson with original json fallback overrides
"""

import json
from typing import Any

_original_dumps = json.dumps
_original_loads = json.loads

try:
    import orjson
    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False


def json_dumps(obj: Any, *args, **kwargs) -> str:
    """
    High-speed serialization using orjson. Falls back to standard json if extra flags are supplied.
    """
    # orjson doesn't support indent parameter directly in keyword args, fallback if kwargs is present
    if HAS_ORJSON and not args and not kwargs:
        try:
            return orjson.dumps(obj).decode("utf-8")
        except Exception:
            pass
            
    # Map 'pretty' custom property if passed explicitly in our own codebase
    if "pretty" in kwargs:
        pretty = kwargs.pop("pretty")
        if pretty:
            kwargs["indent"] = 2
            
    return _original_dumps(obj, *args, **kwargs)


def json_loads(json_str: Any, *args, **kwargs) -> Any:
    """
    Deserializes a JSON string into Python object.
    """
    if HAS_ORJSON and not args and not kwargs and isinstance(json_str, (str, bytes)):
        try:
            return orjson.loads(json_str)
        except Exception:
            pass
            
    return _original_loads(json_str, *args, **kwargs)


def patch_json_globally() -> None:
    """Apply global monkey-patch overrides replacing standard json operations."""
    json.dumps = json_dumps
    json.loads = json_loads
