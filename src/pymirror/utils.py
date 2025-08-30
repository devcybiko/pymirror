import datetime
import os
import re
import sys
from types import SimpleNamespace
from jinja2 import Template, StrictUndefined, Environment, Undefined, DebugUndefined
from .pmlogger import _debug
from dataclasses import fields
from typing import Dict, Any


def snake_to_pascal(snake_str):
    return "".join(word.capitalize() for word in snake_str.split("_"))


def expand_string(s: str, context: dict, dflt: str = None) -> str:
    if not s:
        return s
    if not isinstance(s, str):
        return s
    s = os.path.expandvars(s)
    if "{" in s:
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


##
## This is a proxy class that returns None for any attribute or item access.
## It is used to safely handle missing attributes in SafeNamespace.
##
class _NoneProxy:
    def __getattr__(self, name):
        return _NONE_PROXY

    def __getitem__(self, name):
        return _NONE_PROXY

    def __eq__(self, other):
        return other == None

    def __bool__(self):
        return False

    def __repr__(self):
        return "None"


_NONE_PROXY = _NoneProxy()


## This is a safe namespace class that returns None for any missing attributes.
class SafeNamespace(SimpleNamespace):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            if isinstance(v, dict):
                kwargs[k] = SafeNamespace(**v)
            elif isinstance(v, list):
                kwargs[k] = [
                    SafeNamespace(**i) if isinstance(i, dict) else i for i in v
                ]
        super().__init__(**kwargs)
        self.__dict__.update(kwargs)

    def __getattr__(self, name):
        # Return _NONE_PROXY for missing attributes
        return _NONE_PROXY

    def __getitem__(self, name):
        return getattr(self, name, _NONE_PROXY)


def _add(t, d):
    """Increment each element of the tuple by the corresponding element in d."""
    return tuple(a + b for a, b in zip(t, d))


def _sub(t1, t2):
    """Calculate the difference between two tuples."""
    return tuple(a - b for a, b in zip(t1, t2))


def _scale(t1, s):
    return tuple(x * s for x in t1)


def _div(t1, t2):
    return tuple(x / y for x, y in zip(t1, t2))


def _mul(t1, t2):
    return tuple(x * y for x, y in zip(t1, t2))


def _norm(t1):
    ## take the norm of the tuple
    return sum(x * x for x in t1) ** 0.5


def _height(rect: tuple) -> int:
    return rect[3] - rect[1]


def _width(rect: tuple) -> int:
    return rect[2] - rect[0]


def _str_to_rect(rect: str) -> tuple:
    """Convert a rectangle string to a tuple of floats."""
    if not rect:
        return (0.0, 0.0, 1.0, 1.0)
    try:
        return tuple(float(x) for x in rect.split(","))
    except ValueError as e:
        raise ValueError(f"Invalid rectangle format: {rect}") from e


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


def to_int(s: str, dflt: int = 0) -> int:
    try:
        return int(s)
    except ValueError:
        return dflt


def has_alpha(text):
    """Check if string contains any alphabetic characters"""
    return any(char.isalpha() for char in text)


def non_null(*values: Any) -> Any:
    """Return the first non-null value from the provided arguments."""
    for v in values:
        if v != None:
            return v
    return None


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
    return result

def _replace_year_month_day(word):
    result = re.sub(r"\d{4}-\d{2}-\d{2}", r"%Y-%m-%d", word)
    result = re.sub(r"\d{4}-\d{2}", r"%Y-%m", result)
    return result

def _replace_month_day_year(word):
    result = _replace_month_day(word)
    result = re.sub(r"(%[bB]) (%-d)([ ,]+)\d{4}", r"\1 \2\3%Y", result)
    result = re.sub(r"(%[bB]) (%-d)([ ,]+)\d{2}", r"\1 \2\3%y", result)
    result = re.sub(r"(%[bB]) (%d)([ ,]+)\d{4}", r"\1 \2\3%Y", result)
    result = re.sub(r"(%[bB]) (%d)([ ,]+)\d{2}", r"\1 \2\3%y", result)
    result = re.sub(r"(%[bB]) \d{2}$", r"\1 %d", result)

    result = re.sub(r"(%[bB])-(%-d)-\d{4}", r"\1-\2-%Y", result)
    result = re.sub(r"(%[bB])-(%-d)-\d{2}", r"\1-\2-%y", result)
    result = re.sub(r"(%[bB])-(%d)-\d{4}", r"\1-\2-%Y", result)
    result = re.sub(r"(%[bB])-(%d)-\d{2}", r"\1-\2-%y", result)

    result = re.sub(r"\d{2}/\d{2}/\d{4}", r"%m/%d/%Y", result)
    result = re.sub(r"\d{2}/\d{1}/\d{4}", r"%m/%-d/%Y", result)
    result = re.sub(r"\d{1}/\d{2}/\d{4}", r"%-m/%d/%Y", result)
    result = re.sub(r"\d{1}/\d{1}/\d{4}", r"%-m/%-d/%Y", result)

    result = re.sub(r"\d{2}/\d{2}/\d{2}", r"%m/%d/%y", result)
    result = re.sub(r"\d{1}/\d{2}/\d{2}", r"%-m/%d/%y", result)
    result = re.sub(r"\d{2}/\d{1}/\d{2}", r"%m/%-d/%y", result)
    result = re.sub(r"\d{1}/\d{1}/\d{2}", r"%-m/%-d/%y", result)

    result = re.sub(r"\d{2}/\d{4}", r"%m/%Y", result)

    result = re.sub(r"\d{2}/\d{2}", r"%m/%d", result)
    result = re.sub(r"\d{1}/\d{2}", r"%-m/%d", result)
    result = re.sub(r"\d{2}/\d{1}", r"%m/%-d", result)
    result = re.sub(r"\d{1}/\d{1}", r"%-m/%-d", result)
    return result

def _replace_hours_minutes_seconds(word):
    result = word

    result = re.sub(r"99:\d{2}:\d{2} (am|pm)", r"%H:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"9:\d{2}:\d{2} (am|pm)", r"%-H:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"99:\d{2} (am|pm)", r"%H:%M %p", result, flags=re.IGNORECASE)
    result = re.sub(r"9:\d{2} (am|pm)", r"%-H:%M %p", result, flags=re.IGNORECASE)

    result = re.sub(r"99:\d{2}:\d{2}", r"%H:%M:%S", result)
    result = re.sub(r"9:\d{2}:\d{2}", r"%-H:%M:%S", result)
    result = re.sub(r"99:\d{2}", r"%H:%M", result)
    result = re.sub(r"9:\d{2}", r"%-H:%M", result)

    result = re.sub(r"\d{2}:\d{2}:\d{2} (am|pm)", r"%I:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"\d{1}:\d{2}:\d{2} (am|pm)", r"%-I:%M:%S %p", result, flags=re.IGNORECASE)
    result = re.sub(r"\d{2}:\d{2} (am|pm)", r"%I:%M %p", result, flags=re.IGNORECASE)
    result = re.sub(r"\d{1}:\d{2} (am|pm)", r"%-I:%M %p", result, flags=re.IGNORECASE)

    result = re.sub(r"\d{2}:\d{2}:\d{2}", r"%I:%M:%S", result)
    result = re.sub(r"\d{1}:\d{2}:\d{2}", r"%-I:%M:%S", result)
    result = re.sub(r"\d{2}:\d{2}", r"%I:%M", result)
    result = re.sub(r"\d{1}:\d{2}", r"%-I:%M", result)
    return result

def strftime_by_example(_example: str) -> str:
    """Format a datetime string according to the specified example."""
    ## NOTE: Returns immediately if "%" is in the string, assuming it's already a strftime format
    if "%" in _example:
        return _example
    result = _replace_dow(_example)
    result = _replace_hours_minutes_seconds(result)
    result = _replace_year_month_day(result)
    result = _replace_month_day_year(result)
    example = result.strip()
    return example


if __name__ == "__main__":
    tests = [
        {"test": "Thursday, March 9, 2025", "expected": "Friday, January 2, 1970"},
        {"test": "March 9", "expected": "January 2"},
        {"test": "March 09", "expected": "January 02"},
        {"test": "March 9, 25", "expected": "January 2, 70"},
        {"test": "March 9, 2025", "expected": "January 2, 1970"},
        {"test": "March 09, 25", "expected": "January 02, 70"},
        {"test": "March 09, 2025", "expected": "January 02, 1970"},

        {"test": "Mar-9", "expected": "Jan-2"},
        {"test": "Mar-09", "expected": "Jan-02"},
        {"test": "Mar-9-25", "expected": "Jan-2-70"},
        {"test": "Mar-09-25", "expected": "Jan-02-70"},
        {"test": "Mar-9-2025", "expected": "Jan-2-1970"},
        {"test": "Mar-09-2025", "expected": "Jan-02-1970"},

        {"test": "2025-03-09", "expected": "1970-01-02"},
        {"test": "2025-03", "expected": "1970-01"},

        {"test": "3/9/2025", "expected": "1/2/1970"},
        {"test": "03/9/2025", "expected": "01/2/1970"},
        {"test": "3/09/2025", "expected": "1/02/1970"},
        {"test": "03/09/2025", "expected": "01/02/1970"},
        {"test": "3/9/25", "expected": "1/2/70"},
        {"test": "03/9/25", "expected": "01/2/70"},
        {"test": "3/09/25", "expected": "1/02/70"},
        {"test": "03/09/25", "expected": "01/02/70"},
        {"test": "3/9", "expected": "1/2"},
        {"test": "03/9", "expected": "01/2"},
        {"test": "3/09", "expected": "1/02"},
        {"test": "03/09", "expected": "01/02"},

        {"test": "00:00:00", "expected": "01:02:03"},
        {"test": "Mar 9, 2025 00:00:00", "expected": "Jan 2, 1970 01:02:03"},
        {"test": "March 9, 00:00", "expected": "January 2, 01:02"},
        {"test": "Mar 9, 2025 0:00:00", "expected": "Jan 2, 1970 1:02:03"},
        {"test": "March 9, 0:00", "expected": "January 2, 1:02"},

        {"test": "00:00:00 AM", "expected": "01:02:03 AM"},
        {"test": "Mar 9, 2025 00:00:00 PM", "expected": "Jan 2, 1970 01:02:03 AM"},
        {"test": "March 9, 00:00 am", "expected": "January 2, 01:02 AM"},
        {"test": "Mar 9, 2025 0:00:00 PM", "expected": "Jan 2, 1970 1:02:03 AM"},
        {"test": "March 9, 0:00 AM", "expected": "January 2, 1:02 AM"},

        {"test": "99:00:00", "expected": "01:02:03"},
        {"test": "Mar 9, 2025 99:00:00", "expected": "Jan 2, 1970 01:02:03"},
        {"test": "March 9, 99:00", "expected": "January 2, 01:02"},
        {"test": "Mar 9, 2025 9:00:00", "expected": "Jan 2, 1970 1:02:03"},
        {"test": "March 9, 9:00", "expected": "January 2, 1:02"},

        {"test": "99:00:00 AM", "expected": "01:02:03 AM"},
        {"test": "Mar 9, 2025 99:00:00 PM", "expected": "Jan 2, 1970 01:02:03 AM"},
        {"test": "March 9, 99:00 am", "expected": "January 2, 01:02 AM"},
        {"test": "Mar 9, 2025 9:00:00 PM", "expected": "Jan 2, 1970 1:02:03 AM"},
        {"test": "March 9, 9:00 AM", "expected": "January 2, 1:02 AM"},

        {"test": "Mar-9 0:00 pm", "expected": "Jan-2 1:02 AM"},
    ]
    tests2 = [
        {"test": "99:00:00", "expected": "13:02:03"},
        {"test": "Mar 9, 2025 99:00:00", "expected": "Jan 2, 1970 13:02:03"},
        {"test": "March 9, 99:00", "expected": "January 2, 13:02"},
        {"test": "Mar 9, 2025 9:00:00", "expected": "Jan 2, 1970 13:02:03"},
        {"test": "March 9, 9:00", "expected": "January 2, 13:02"},

        {"test": "99:00:00 AM", "expected": "13:02:03 PM"},
        {"test": "Mar 9, 2025 99:00:00 PM", "expected": "Jan 2, 1970 13:02:03 PM"},
        {"test": "March 9, 99:00 am", "expected": "January 2, 13:02 PM"},
        {"test": "Mar 9, 2025 9:00:00 PM", "expected": "Jan 2, 1970 13:02:03 PM"},
        {"test": "March 9, 9:00 AM", "expected": "January 2, 13:02 PM"},
    ]


    test_date_time = datetime.datetime.strptime("1/2/1970T01:02:03", "%m/%d/%YT%I:%M:%S")
    for test in tests:
        strftime = strftime_by_example(test["test"])
        result = test_date_time.strftime(strftime)
        if result != test["expected"]:
            print(f"Test failed for '{test['test']}->{strftime}': expected '{test['expected']}', got '{result}'")
            sys.exit(1)

    print("-- PM TESTS--")
    test_date_time2 = datetime.datetime.strptime("1/2/1970T13:02:03", "%m/%d/%YT%H:%M:%S")
    for test in tests2:
        strftime = strftime_by_example(test["test"])
        result = test_date_time2.strftime(strftime)
        if result != test["expected"]:
            print(f"Test failed for '{test['test']}->{strftime}': expected '{test['expected']}', got '{result}'")
            sys.exit(1)
        # print(
        #     test,
        #     "->",
        #     strftime,
        #     "->",
        #     test_date_time.strftime(strftime),
        # )
