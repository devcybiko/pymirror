from datetime import datetime, timedelta
import sys
from glslib.logger import _die, _debug

## this is set whenver exemplar_date_time is called, so that strftime_by_example can use it without needing to pass the patterns around everywhere
global __default_patterns # see below...

def exemplar_date_time(exemplar: datetime, include_am_pm=True, case_insensitive=False) -> datetime:
    """
    Given an example datetime object, return a dict for transforming a string in that format to a datetime object.
    """
    global __default_patterns
    year = exemplar.year
    month = exemplar.month
    day = exemplar.day
    hour = exemplar.hour
    minute = exemplar.minute
    second = exemplar.second
    yr = year % 100
    assert year >= 1000, f"Year {year} must be >= 1000 to differeniate from month, day, hours, minutes, seconds"
    assert 1 <= month <= 9, f"Month {month} must be between 1 and 9 for exemplar-based datetime parsing"
    assert 1 <= day <= 9, f"Day {day} must be between 1 and 9 for exemplar-based datetime parsing"
    assert 13 <= hour <= 21, f"Hour {hour} must be between 13 and 21 (1pm-9pm) for exemplar-based datetime parsing"
    assert 0 <= minute <= 9, f"Minute {minute} must be between 0 and 9 for exemplar-based datetime parsing"
    assert 0 <= second <= 9, f"Second {second} must be between 0 and 9 for exemplar-based datetime parsing"
    numbers = set()
    values = [month, day, year, hour, minute, second, yr]
    numbers.update(values)
    assert len(numbers) == 7, f"All the numbers must be unique {values}"
    Mon_name = exemplar.strftime("%b")
    mon_name = Mon_name.lower()
    MON_NAME = Mon_name.upper()
    Month_name = exemplar.strftime("%B")
    month_name = Month_name.lower()
    MONTH_NAME = Month_name.upper()
    patterns = [
        ("Tue", "%a"), # abbreviated weekday name
        ("Tuesday", "%A"), # full weekday name
        (f"{year:04d}", "%Y"), # 4-digit year
        (f"{yr:02d}", "%y"), # 2-digit year
        (Month_name, "%B"), # July
        (Mon_name, "%b"), # Jul
        (f"{month:1d}", "%-m"), # month non-zero padded (1-9)
        (f"{month:02d}", "%m"), # month zero padded (01-09)
        (f"{day:02d}", "%d"), # day zero padded (01-09)
        (f"{day:1d}", "%-d"), # day non-zero padded (1-9)
        (f"{hour:02d}", "%H"), # 24-hr hours (13-21)
        (f"{hour%12:02d}", "%I"), # 12-hours zero padded (01-12)
        (f"{(hour%12):1d}", "%-I"), # 12-hours non-zero padded (1-12)
        (f"{minute:02d}", "%M"), # minute zero padded (00-09)
        (f"{minute:1d}", "%-M"),# minute non-zero padded (0-9)
        (f"{second:02d}", "%S"), # second zero padded (00-09)
        (f"{second:1d}", "%-S"), # second non-zero padded (0-9) 
    ]
    if case_insensitive:
        patterns += [
            ("tue", "%a"), # abbreviated weekday name
            ("tuesday", "%A"), # full weekday name
            (month_name, "%B"), # july
            (MONTH_NAME, "%B"), # JULY
            (mon_name, "%b"), # jul
            (MON_NAME, "%b"), # JUL
        ]
    if include_am_pm:
        patterns += [
            ("pm", "%p"), # am/pm lowercase
            ("PM", "%p"), # am/pm uppercase
            ("am", "%p"), # am/pm lowercase
            ("AM", "%p"), # am/pm uppercase
        ]

    # Return in order of longest match to shortest to ensure correct parsing
    patterns = sorted(patterns, key=lambda x: len(x[0]), reverse=True)
    __default_patterns = patterns # set the global default patterns so that strftime_by_example can use them without needing to pass the patterns around everywhere
    return patterns

__default_patterns = exemplar_date_time(datetime(1776, 7, 4, 13, 2, 3))


def strftime_by_example(example: str, patterns: list=None, verify=False) -> str:
    """
    given an example string and a list of (pattern, strftime_code) tuples, replace occurrences of the patterns in the example with the corresponding strftime codes
    """
    if patterns is None:
        global __default_patterns
        if __default_patterns is None:
            raise ValueError("No patterns provided and no default patterns set. Call exemplar_data_time with an exemplar datetime to set the default patterns.")
        patterns = __default_patterns
    if '%' in example:
        # it likely is already a strftime format, so just return it as is to avoid double-replacing
        return example
    result = example
    for pattern, code in patterns:
        result = result.replace(pattern, code)
    if verify:
        try:
            datetime.strptime(example, result)
        except Exception as e:
            print(e, file=sys.stderr)
            raise ValueError(f"\nFailed to parse example '{example}' with format '{result}'\nCheck for redundant values.")
    return result

def test():
    exemplar = datetime.strptime("1776-07-04 13:02:03", "%Y-%m-%d %H:%M:%S")
    patterns = exemplar_date_time(exemplar)
    print(f"Exemplar: {exemplar}")
    print(f"Patterns: {patterns}")

    examples = [
        "1776-07-04 13:02:03",
        "07/04/1776 1:02:03 PM",
        "Saturday: July 4, 1776 13:02:03",
        "Sat: 4 Jul 1776 13:02:03",
        "1776/7/4 13:2:3",
        "7-4-1776 13:02:03",
        "1776.07.04 13:02:03",
        "04 Jul 1776 13:02:03",
        "Jul 4, 1776 1:02:03 PM",
        ]
    for example in examples:
        format = strftime_by_example(example, patterns)
        print(f"Exemplar: {example} -> Format string: {format}")
        assert datetime.strptime(example, format) == datetime(1776, 7, 4, 13, 2, 3), f"Failed to parse {example} with format {format}"

    # times without seconds
    examples = [
        "1776-07-04 13:02",
        "07/04/1776 1:02 PM",
        "July 4, 1776 13:02",
        "4 Jul 1776 13:02",
        "1776/7/4 13:2",
        "7-4-1776 13:02",
        "1776.07.04 13:02",
        "04 Jul 1776 13:02",
        "Jul 4, 1776 1:02 PM",
    ]
    for example in examples:
        format = strftime_by_example(example, patterns)
        print(f"Exemplar: {example} -> Format string: {format}")
        assert datetime.strptime(example, format) == datetime(1776, 7, 4, 13, 2), f"Failed to parse {example} with format {format}"

    # dates with abbreviated years
    examples = [
        "76-07-04 13:02:03",
        "07/04/76 1:02:03 PM",
        "Jul 4, 76 1:02:03 PM",
    ]
    for example in examples:
        format = strftime_by_example(example, patterns)
        print(f"Exemplar: {example} -> Format string: {format}")
        assert datetime.strptime(example, format) == datetime(1976, 7, 4, 13, 2, 3), f"Failed to parse {example} with format {format}"

    # just dates
    examples = [
        "1776-07-04",
        "07/04/1776",
        "July 4, 1776",
        "4 Jul 1776",
        "1776/7/4",
        "7-4-1776",
        "1776.07.04",
        "04 Jul 1776",
        "Jul 4, 1776",
    ]
    for example in examples:
        format = strftime_by_example(example, patterns)
        print(f"Exemplar: {example} -> Format string: {format}")
        assert datetime.strptime(example, format) == datetime(1776, 7, 4), f"Failed to parse {example} with format {format}"
    
    ## just morning times
    examples = [
        "01:02:03",
        "1:2:3",
    ]
    for example in examples:
        format = strftime_by_example(example, patterns)
        print(f"Exemplar: {example} -> Format string: {format}")
        assert datetime.strptime(example, format).time() == datetime(1776, 7, 4, 1, 2, 3).time(), f"Failed to parse {example} with format {format}"

    ## just afternoon times
    examples = [
        "13:02:03",
        "01:02:03 PM",
    ]
    for example in examples:
        format = strftime_by_example(example, patterns)
        print(f"Exemplar: {example} -> Format string: {format}")
        assert datetime.strptime(example, format).time() == datetime(1776, 7, 4, 13, 2, 3).time(), f"Failed to parse {example} with format {format}"

    strftime = strftime_by_example("   Your Favorite Date: July 4, 1776 1:02:03 PM", patterns)
    a = datetime.now().strftime(strftime)
    print(f"Custom format: {strftime} -> \n{a}")

    strftime = strftime_by_example("   Your Favorite Time: (Saturday) 13:02Z", patterns)
    a = datetime.now().strftime(strftime)
    print(f"Custom format: {strftime} -> \n{a}")

    ## turn off verification to allow for unusual formats that might have redundant values
    strftime = strftime_by_example("   Hey! I wasn't born: Saturday: July 4, 1776, (1776-07-04)", patterns, verify=False)
    yesterday = (datetime.now() - timedelta(days=1)).strftime(strftime)
    print(f"Custom format: {strftime} -> \n{yesterday}")

if __name__ == "__main__":
    test()