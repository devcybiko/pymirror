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

def _strftime_by_example(_example: str, verify=False) -> str:
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

def _replace_00_00_00(word):
    result = re.sub(r"12:00:00 PM", "%H:%M:%S %p", word)
    result = re.sub(r"12:00:00", "%H:%M:%S", word)
    result = re.sub(r"0:00:00", "%-H:%M:%S", result)
    result = re.sub(r"00:00", "%H:%M", result)
    result = re.sub(r"0:00", "%-H:%M", result)
    return result

def _replace_year(word):
    result = re.sub(r"1776", "%Y", word, flags=re.IGNORECASE)
    result = re.sub(r"76", "%y", result, flags=re.IGNORECASE)
    return result

def _replace_month(word):
    result = re.sub(r"july", "%B", word, flags=re.IGNORECASE)
    result = re.sub(r"jul", "%b", result, flags=re.IGNORECASE)
    result = re.sub(r"07", "%m", result)
    result = re.sub(r"7", "%-m", result)
    return result

def _replace_day(word):
    result = re.sub(r"04", "%d", word)
    result = re.sub(r"4", "%-d", result)
    return result

def _replace_hours(word):
    result = re.sub(r"01", "%I", word)
    result = re.sub(r"13", "%H", result)
    result = re.sub(r"23", "%-H", result)
    result = re.sub(r"1", "%-I", result)
    return result

def _replace_mins(word):
    result = re.sub(r"02", "%M", word)
    result = re.sub(r"2", "%-M", result)
    return result

def _replace_secs(word):
    result = re.sub(r"03", "%S", word)
    result = re.sub(r"3", "%-S", result)
    return result

def _replace_pm(word):
    result = re.sub(r"PM", "%p", word)
    result = re.sub(r"pm", "%p", result)
    return result


def strftime_by_example(example: str, verify=False) -> str:
    """
    Format a datetime string according to the specified example.
    DATES: July 4, 1776 - use as the example date.
        76 - use as the example 2-digit year.
        1776 - use as the example 4-digit year.
        July or Jul - use as the example month.
        07 - use as the example 2-digit month.
        7 - use as the example 1-digit month.
        04 - use as the example 2-digit day.
        4 - use as the example 1-digit day.

    TIMES: exampler time is 1:02:03 PM
        1 - example hour (single-digit)
        01 - example hour (zero-padded)
        2 - example minute (single-digit)
        02 - example minute (zero-padded)
        3 - example second (single-digit)
        03 - example second (zero-padded)
        ? - example 24-hour clock hour (zero-padded)
        13 - example 24-hour clock hour (single-digit)
        23 - example 24-hour clock hour (zero-padded)
        PM - use as the example for 12-hour clock with AM/PM
    """
    result = example
    result = _replace_year(result)
    result = _replace_dow(result)
    result = _replace_december(result)
    result = _replace_1969(result)
    return result

def exemplar_data_time(exemplar: datetime) -> datetime:
    """
    Given an example datetime object, return a dict for transforming a string in that format to a datetime object.
    """
    year = exemplar.year
    month = exemplar.month
    day = exemplar.day
    hour = exemplar.hour
    minute = exemplar.minute
    second = exemplar.second
    yr = year % 100
    assert year < 1000, f"Year {year} must be >= 1000 to differeniate from month, day, hours, minutes, seconds"
    assert 1 <= month <= 9, f"Month {month} must be between 1 and 9 for exemplar-based datetime parsing"
    assert 1 <= day <= 9, f"Day {day} must be between 1 and 9 for exemplar-based datetime parsing"
    assert 0 <= hour <= 9, f"Hour {hour} must be between 0 and 9 for exemplar-based datetime parsing"
    assert 0 <= minute <= 9, f"Minute {minute} must be between 0 and 9 for exemplar-based datetime parsing"
    assert 0 <= second <= 9, f"Second {second} must be between 0 and 9 for exemplar-based datetime parsing"
    numbers = set()
    values = [month, day, year, hour, minute, second, yr]
    numbers.update(values)
    assert len(numbers) == 7, f"All the numbers must be unique {values}"
    return {
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "minute": minute,
        "second": second,
        "yr": yr
    }

def main():
    exemplar = "1776-07-04 13:02:03"
    format = exemplar_data_time(exemplar)
    print(f"Example: {exemplar}")
    print(f"Format: {format}")