from libs.glslib.strings import strftime_by_example
from datetime import datetime, timedelta

def main():
    date_examples = [
        "2024-06-30",
        "06/30/2024",
        "6/30/2024",
        "2024/06/30",
        "2024/6/30",
        "Sun, Jun 30, 2024",
        "Sun, Jun-30, 2024",
        "Sun Jun 30 2024",
        "Jun 30, 2024",
        "2024-06-30",
        "06/30/2024",
        "6/30/2024",
        # "24/06/30",
        # "24/6/30",
        "Sun, Jun 30, 24",
        "Sun, Jun-30, 24",
        "Sun Jun 30 24",
        "Jun 30, 24",
        "6/30/24",
        "06/30/24",
    ]
    expected_date = datetime(2024, 6, 30)
    for example in date_examples:
        format_str = strftime_by_example(example)
        print(f"Example: {example} -> Format: {format_str}")
        parsed_date = datetime.strptime(example, format_str)
        print(f"    -> Parsed: {datetime.strptime(example, format_str)}  ")
        assert parsed_date == expected_date

    morning_time_examples = [
        "2024-06-30 9:00 AM",
        "6/30/2024 9:00 AM",
        "2024-06-30 09:00 AM",
        "6/30/2024 09:00 AM",
    ]
    expected_date_time = datetime(2024, 6, 30, 9, 0)
    for example in morning_time_examples:
        format_str = strftime_by_example(example)
        print(f"Example: {example} -> Format: {format_str}")
        parsed_date = datetime.strptime(example, format_str)
        print(f"    -> Parsed: {datetime.strptime(example, format_str)}  ")
        assert parsed_date == expected_date_time

    afternoon_time_examples = [
        "2024-06-30 9:00 PM",
        "6/30/2024 9:00 PM",
        "2024-06-30 09:00 PM",
        "6/30/2024 21:00",
        "6/30/2024 09:00 PM",
    ]
    expected_afternoon_time = datetime(2024, 6, 30, 21, 0)
    for example in afternoon_time_examples:
        format_str = strftime_by_example(example)
        print(f"Example: {example} -> Format: {format_str}")
        parsed_date = datetime.strptime(example, format_str)
        print(f"    -> Parsed: {datetime.strptime(example, format_str)}  ")
        assert parsed_date == expected_afternoon_time
if __name__ == "__main__":
    main()

