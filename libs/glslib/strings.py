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

def _replace_month(word):
    result = re.sub(r"january|february|march|april|may|june|july|august|september|october|november|december", "%B", word, flags=re.IGNORECASE)
    result = re.sub(r"jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec", "%b", result, flags=re.IGNORECASE)
    return result

def _replace_dow(word):
    result = re.sub(r"monday|tuesday|wednesday|thursday|friday|saturday|sunday", "%A", word, flags=re.IGNORECASE)
    result = re.sub(r"mon|tue|wed|thu|fri|sat|sun", "%a", result, flags=re.IGNORECASE)
    return result

def _replace_month_day(word):
    result = _replace_month(word)
    result = re.sub(r"(%[bB]) \d{2}([^0-9])", r"\1 %d\2", result)
    result = re.sub(r"(%[bB]) \d{2}$", r"\1 %d", result)
    result = re.sub(r"(%[bB]) \d{1}([^0-9])", r"\1 %-d\2", result)
    result = re.sub(r"(%[bB]) \d{1}$", r"\1 %-d", result)

    result = re.sub(r"(%[bB])-\d{2}([^0-9])", r"\1-%d\2", result)
    result = re.sub(r"(%[bB])-\d{2}$", r"\1-%d", result)
    result = re.sub(r"(%[bB])-\d{1}([^0-9])", r"\1-%-d\2", result)
    result = re.sub(r"(%[bB])-\d{1}$", r"\1-%-d", result)

    result = re.sub(r"(%[bB])/\d{2}([^0-9])", r"\1/%d\2", result)
    result = re.sub(r"(%[bB])/\d{2}$", r"\1/%d", result)
    result = re.sub(r"(%[bB])/\d{1}([^0-9])", r"\1/%-d\2", result)
    result = re.sub(r"(%[bB])/\d{1}$", r"\1/%-d", result)

    result = re.sub(r"\d{2}-\d{2}([^0-9])", r"%m-%d\1", result)
    result = re.sub(r"\d{2}-\d{2}$", r"%m-%d", result)
    result = re.sub(r"\d{1}-\d{1}([^0-9])", r"%-m-%-d\1", result)
    result = re.sub(r"\d{1}-\d{1}$", r"%-m-%-d", result)

    result = re.sub(r"\d{2}/\d{2}([^0-9])", r"%m/%d\1", result)
    result = re.sub(r"\d{2}/\d{2}$", r"%m/%d", result)
    result = re.sub(r"\d{1}/\d{1}([^0-9])", r"%-m/%-d\1", result)
    result = re.sub(r"\d{1}/\d{1}$", r"%-m/%-d", result)

    return result

def _replace_year_month_day(word):
    result = re.sub(r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d", word)
    result = re.sub(r"\d{4}/\d{2}/\d{2}", "%Y/%m/%d", result)
    result = re.sub(r"\d{4}-\d{1}-\d{2}", "%Y-%-m-%d", result)
    result = re.sub(r"\d{4}/\d{1}/\d{2}", "%Y/%-m/%d", result)
    result = re.sub(r"\d{4}-\d{2}-\d{1}", "%Y-%m-%-d", result)
    result = re.sub(r"\d{4}/\d{2}/\d{1}", "%Y/%m/%-d", result)
    return result

def _replace_month_day_year(word):
    result = re.sub(r"\d{2}-\d{2}-\d{4}", r"%m-%d-%Y", word)
    result = re.sub(r"\d{2}/\d{2}/\d{4}", r"%m/%d/%Y", result)
    result = re.sub(r"\d{1}-\d{2}-\d{4}", r"%-m-%d-%Y", result)
    result = re.sub(r"\d{1}/\d{2}/\d{4}", r"%-m/%d/%Y", result)
    result = re.sub(r"\d{2}-\d{1}-\d{4}", r"%m-%-d-%Y", result)
    result = re.sub(r"\d{2}/\d{1}/\d{4}", r"%m/%-d/%Y", result)
    result = re.sub(r"\d{1}-\d{1}-\d{4}", r"%-m-%-d-%Y", result)
    result = re.sub(r"\d{1}/\d{1}/\d{4}", r"%-m/%-d/%Y", result)
    result = re.sub(r"\d{2}-\d{2}-\d{2}", r"%m-%d-%y", result)
    result = re.sub(r"\d{2}/\d{2}/\d{2}", r"%m/%d/%y", result)
    result = re.sub(r"\d{1}-\d{2}-\d{2}", r"%-m-%d-%y", result)
    result = re.sub(r"\d{1}/\d{2}/\d{2}", r"%-m/%d/%y", result)
    result = re.sub(r"\d{2}-\d{1}-\d{2}", r"%m-%-d-%y", result)
    result = re.sub(r"\d{2}/\d{1}/\d{2}", r"%m/%-d/%y", result)
    result = re.sub(r"\d{1}-\d{1}-\d{2}", r"%-m-%-d-%y", result)
    result = re.sub(r"\d{1}/\d{1}/\d{2}", r"%-m/%-d/%y", result)
    return result

def _replace_hours_minutes_seconds(word):
    result = word

    result = re.sub(r"99:\d{2}:\d{2} (am|pm)", r"%I:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"9:\d{2}:\d{2} (am|pm)", r"%-I:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"99:\d{2} (am|pm)", r"%I:%M %p", result, flags=re.IGNORECASE)
    result = re.sub(r"9:\d{2} (am|pm)", r"%-I:%M %p", result, flags=re.IGNORECASE)

    result = re.sub(r"99:\d{2}:\d{2}", r"%H:%M:%S", result)
    result = re.sub(r"9:\d{2}:\d{2}", r"%-H:%M:%S", result)
    result = re.sub(r"99:\d{2}", r"%H:%M", result)
    result = re.sub(r"9:\d{2}", r"%-H:%M", result)

    result = re.sub(r"\d{2}:\d{2}:\d{2} (am|pm)", r"%I:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"\d{1}:\d{2}:\d{2} (am|pm)", r"%-I:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"\d{2}:\d{2} (am|pm)", r"%I:%M %p", result, flags=re.IGNORECASE)
    result = re.sub(r"\d{1}:\d{2} (am|pm)", r"%-I:%M %p", result, flags=re.IGNORECASE)

    result = re.sub(r"\d{2}:\d{2}:\d{2}", r"%H:%M:%S", result)
    result = re.sub(r"\d{1}:\d{2}:\d{2}", r"%-H:%M:%S", result)
    result = re.sub(r"\d{2}:\d{2}", r"%H:%M", result)
    result = re.sub(r"\d{1}:\d{2}", r"%-H:%M", result)
    return result

def _replace_year(word):
    result = re.sub(r"\d{4}", r"%Y", word)
    result = re.sub(r"\d{2}", r"%y", result)
    return result

def _replace_day(word):
    # Month is already replaced, so just replace remaining day numbers
    # Replace 2-digit numbers (01-31) after a month with %d
    result = re.sub(r"(?<=%[bB] )\d{2}", r"%d", word)
    result = re.sub(r"(?<=%[bB]-)\d{2}", r"%d", result)
    # Replace 1-digit numbers (1-9) after a month with %-d
    result = re.sub(r"(?<=%[bB] )\d{1}", r"%-d", result)
    result = re.sub(r"(?<=%[bB]-)\d{1}", r"%-d", result)
    # Replace 2-digit numbers (01-31) before a month with %d
    result = re.sub(r"\d{2}(?= %?[bB])", r"%d", result)
    result = re.sub(r"\d{2}(?=-%?[bB])", r"%d", result)
    # Replace 1-digit numbers (1-9) before a month with %-d
    result = re.sub(r"\d{1}(?= %?[bB])", r"%-d", result)
    result = re.sub(r"\d{1}(?=-%?[bB])", r"%-d", result)
    return result

def strftime_by_example(_example: str, verify=False) -> str:
    """Format a datetime string according to the specified example."""
    ## NOTE: Returns immediately if "%" is in the string, assuming it's already a strftime format
    if "%" in _example:
        return _example
    # print(f"{_example}...")
    format = _replace_dow(_example)
    # print(219, f"...{result}")
    format = _replace_hours_minutes_seconds(format)
    # print(221, f"...{result}")
    format = _replace_year_month_day(format)
    # print(223,f"...{result}")
    format = _replace_month_day_year(format)
    # print(225,f"...{result}")
    format = _replace_month_day(format)
    # print(226,f"...{result}")
    format = _replace_month(format)
    # print(227,f"...{result}")
    format = _replace_day(format)
    # print(229,f"...{result}")
    format = _replace_year(format)
    # print(231,f"...{result}")
    if verify:
        ## Test the resulting format string by trying to parse the original example
        parsed_date = datetime.strptime(_example, format)
        assert parsed_date.strftime(format) == _example, f"Verification failed: {parsed_date.strftime(format)} != {_example}"

    return format
