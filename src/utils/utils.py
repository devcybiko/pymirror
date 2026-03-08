import pprint as _pprint
from munch import DefaultMunch, Munch
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any
import hashlib


def non_null(*values: Any) -> Any:
    """Return the first non-null value from the provided arguments."""
    for v in values:
        if v != None:
            return v
    return None

def pprint(obj):
    if isinstance(obj, Munch):
        _pprint.pprint(obj.toDict(), indent=2, width=80)
    elif is_dataclass(obj):
        pprint(asdict(obj))
    elif hasattr(obj, '__dict__'):
        print(f"=== {obj.__class__.__name__} Object Members ===")
        print(f"Type: {type(obj).__name__}")
        print("Instance attributes:")
        _pprint.pprint(vars(obj), indent=2, width=80)
    else:
        # Fallback for objects without __dict__ (built-in types, etc.)
        _pprint.pprint(obj, indent=2, width=80)

def print_class_hierarchy(obj):
    print("Class hierarchy:")
    for cls in obj.__class__.__mro__:
        print(cls.__name__)

def make_hashcode(*args):
    s = "|".join(str(a) for a in args)
    return hashlib.sha256(s.encode()).hexdigest()

def munchify(obj):
    if isinstance(obj, dict):
        return DefaultMunch.fromDict({k: munchify(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return [munchify(v) for v in obj]
    else:
        return obj

