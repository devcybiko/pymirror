from .logger import _trace, _error, _print
from munch import DefaultMunch, Munch, munchify
from dataclasses import is_dataclass
import datetime
import sys

def to_list(s: str | list) -> list:
    if type(s) == list:
        return s
    return [s]

def to_int(s: str, dflt: int = 0) -> int:
    try:
        return int(s)
    except ValueError as e:
        return dflt

def to_float(s: str, dflt: float = 0.0) -> float:
    try:
        return float(s)
    except ValueError:
        return dflt

def to_munch(obj):
    if isinstance(obj, dict):
        return DefaultMunch.fromDict({k: munchify(v) for k, v in obj.items()})
    elif isinstance(obj, list):
        return [munchify(v) for v in obj]
    else:
        return obj

def to_secs(s: str, dflt_secs: int = 0) -> int:
    return to_ms(s, dflt_secs * 1000) // 1000

def to_ms(s: str, dflt: int = 0) -> int:
    _trace("s", s)
    if type(s) == int or type(s) == float:
        _trace("type(s)", type(s))
        return int(s)
    if len(s) == 0:
        # empty string == 0 ms
        _trace("empty string")
        return dflt
    if len(s) == 1:
        # single digit == n ms
        _trace("single digit", s)
        return to_int(s, dflt)
    if s[-2] == "ms":
        # milliseconds
        _trace("milliseconds", s)
        return to_int(s[0:-2], dflt)
    if s[-1] == "s":
        # seconds
        _trace("seconds", s, s[:-1])
        return to_int(s[:-1], dflt) * 1000
    if s[-1] == "m":
        minutes = to_int(s[:-1], dflt) * 60 * 1000
        _trace("minutes", s, s[:-1], minutes)
        return minutes
    if s[-1] == "h":
        _trace("hours", s, s[:-1])
        return to_float(s[:-1], dflt) * 60 * 60 * 1000
    return to_int(s, dflt)

def to_utc_epoch(dt) -> float:
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=datetime.timezone.utc)
    else:
        # Convert aware datetime to UTC
        dt = dt.astimezone(datetime.timezone.utc)
    return dt.timestamp()

def to_dict(obj) -> dict:
    """Convert any object to dict recursively"""
    if is_dataclass(obj):
        # Use __dict__ instead of asdict() to capture all attributes
        result = {}
        for key, value in obj.__dict__.items():
            result[key] = to_dict(value)
        return result
    if isinstance(obj, Munch):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, '__table__'):
        return obj.__dict__
    elif isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [to_dict(item) for item in obj]
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return obj

def to_naive(dt):
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

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
            _print(f"Test failed for '{test['test']}->{strftime}': expected '{test['expected']}', got '{result}'")
            sys.exit(1)

    _print("-- PM TESTS--")
    test_date_time2 = datetime.datetime.strptime("1/2/1970T13:02:03", "%m/%d/%YT%H:%M:%S")
    for test in tests2:
        strftime = strftime_by_example(test["test"])
        result = test_date_time2.strftime(strftime)
        if result != test["expected"]:
            _error(f"Test failed for '{test['test']}->{strftime}': expected '{test['expected']}', got '{result}'")
            sys.exit(1)
        # _print(
        #     test,
        #     "->",
        #     strftime,
        #     "->",
        #     test_date_time.strftime(strftime),
        # )
