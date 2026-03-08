import pprint as _pprint
from munch import DefaultMunch, Munch
from dataclasses import asdict, is_dataclass
from typing import Any
import hashlib


def non_null(*values: Any) -> Any:
    """Return the first non-null value from the provided arguments."""
    for v in values:
        if v != None:
            return v
    return None

def make_hashcode(*args):
    s = "|".join(str(a) for a in args)
    return hashlib.sha256(s.encode()).hexdigest()


