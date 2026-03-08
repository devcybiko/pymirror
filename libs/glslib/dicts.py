from dataclasses import fields
from typing import Dict, Any
from munch import DefaultMunch

def getter(obj, path, default=None):
    keys = path.split(".")
    current = obj
    for key in keys:
        _debug(f"Accessing key: {key} in {current}")
        if isinstance(current, dict):
            current = current.get(key, default)
        elif isinstance(current, list):
            current = current[int(key)]
        else:
            return default
    return current


def from_dict(cls):
    """Decorator to add from_dict class method to any dataclass"""

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]):
        """Create instance from dict, ignoring extra keys"""
        valid_fields = {f.name for f in fields(cls)}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        return cls(**filtered_dict)

    cls.from_dict = from_dict
    return cls

def munchify(obj):
    if isinstance(obj, dict):
        return DefaultMunch.fromDict({k: munchify(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return [munchify(v) for v in obj]
    else:
        return obj