from dataclasses import dataclass, is_dataclass, fields
from datetime import datetime, timedelta
from jinja2 import Environment, DebugUndefined
import os
import re

def snake_to_pascal(snake_str):
    return "".join(word.capitalize() for word in snake_str.split("_"))

def pascal_to_snake(pascal_str):
    result = ""
    under = ""
    for c in pascal_str:
        if c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            result += under + c.lower()
            under = "_"
        else:
            result += c
    return result

def expand_string(s: str, context: dict, dflt: str = None) -> str:
    if not s:
        return s
    if not isinstance(s, str):
        return s
    s = os.path.expandvars(s)
    env = Environment(undefined=DebugUndefined)
    template = env.from_string(s)
    try:
        s = template.render(**context)
    except Exception as e:
        # _debug(f"Error rendering string '{s}' with context {context}: {e}")
        return dflt if dflt is not None else s
    return s

def expand_dict(config: dict, context: dict, dflt: str = None):
    ## recursively expand environment variables in the config dictionary
    for key, value in config.items():
        if isinstance(value, str):
            config[key] = expand_string(value, context, dflt)
        elif isinstance(value, dict):
            expand_dict(value, context, dflt)
        elif isinstance(value, list):
            for i in range(len(value)):
                if isinstance(value[i], str):
                    value[i] = expand_string(value[i], context, dflt)
                elif isinstance(value[i], dict):
                    expand_dict(value[i], context, dflt)

def expand_dataclass(obj, context: dict, dflt: str = None):
    """Recursively expand environment variables in a dataclass object"""
    if is_dataclass(obj):
        # Handle dataclass objects
        for field in fields(obj):
            field_name = field.name
            if hasattr(obj, field_name):
                field_value = getattr(obj, field_name)
                
                if isinstance(field_value, str):
                    # Expand string values
                    expanded_value = expand_string(field_value, context, dflt)
                    setattr(obj, field_name, expanded_value)
                    
                elif is_dataclass(field_value):
                    # Recursively handle nested dataclasses
                    expand_dataclass(field_value, context, dflt)
                    
                elif isinstance(field_value, dict):
                    # Handle dict fields using existing expand_dict function
                    expand_dict(field_value, context, dflt)
                    
                elif isinstance(field_value, list):
                    # Handle list fields
                    for i in range(len(field_value)):
                        item = field_value[i]
                        if isinstance(item, str):
                            field_value[i] = expand_string(item, context, dflt)
                        elif is_dataclass(item):
                            expand_dataclass(item, context, dflt)
                        elif isinstance(item, dict):
                            expand_dict(item, context, dflt)
    
    elif isinstance(obj, dict):
        # Fallback to dict handling for backward compatibility
        expand_dict(obj, context, dflt)
    
    else:
        # For other types, do nothing
        pass

def has_alpha(text):
    """Check if string contains any alphabetic characters"""
    return any(char.isalpha() for char in text)

@dataclass
class Glyphs:
    yes = '\u25CF'
    no = '\u25CB'
    up = '\u25B2'
    down = '\u25BD'
    debug = '\u00A4'

glyphs = Glyphs()

