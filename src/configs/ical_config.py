from dataclasses import dataclass, field

from utils.utils import strftime_by_example

@dataclass
class IcalConfig:
    calendar_name: str = "gregs_calendar"
    title: str = "iCalendar"
    refresh_time: str = "60m"
    max_events: int = 10
    number_days: int = 7
    title_format: str = strftime_by_example("Jan 2025")
    time_format: str = strftime_by_example("0:00 PM")
    show_regular_events: bool = True
    show_all_day_events: bool = True
    show_recurring_events: bool = True
    all_day_format: str = strftime_by_example("Jan-1")
    render_mode: str = "card"
    week_mode: int = 7
    rows: int = None
    holiday_files: list = field(default_factory=list)
    prev_weeks: int = 0
