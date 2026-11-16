"""Serialization helpers for dataclasses and simulation results.

Transforms structured domain models and nested dataclass trees into
JSON-compliant dictionaries ready for HTTP response serialization.
"""

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Union


def to_dict(obj: Any) -> Any:
    """Recursively convert dataclass instances, collections, and primitives into JSON-safe dicts."""
    if is_dataclass(obj):
        # asdict recursively converts nested dataclasses
        return asdict(obj)
    elif isinstance(obj, dict):
        return {str(k): to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple, set)):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, (int, float, str, bool)) or obj is None:
        return obj
    else:
        # Fallback for custom objects with a to_dict() method or string representation
        if hasattr(obj, "to_dict") and callable(getattr(obj, "to_dict")):
            return obj.to_dict()
        return str(obj)
