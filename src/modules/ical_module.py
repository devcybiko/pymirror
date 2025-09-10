# ical_module.py
# https://openicalmap.org/api/one-call-3#current

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
from ics import Calendar

from pymirror.pmcard import PMCard
from pymirror.pmwebapi import PMWebApi
from pymirror.utils import SafeNamespace, strftime_by_example
from pymirror.pmlogger import _debug, _error
from pymirror.ical_parser import IcalParser

@dataclass
class ICalConfig:
    url: str = None
    title: str = "iCalendar"
    cache_file: str = "./caches/ical.json"
    refresh_minutes: int = 60
    max_events: int = 10
    number_days: int = 7
    title_format: str = strftime_by_example("Jan 2025")
    time_format: str = strftime_by_example("0:00 PM")
    show_regular_events: bool = True
    show_all_day_events: bool = True
    show_recurring_events: bool = True
    all_day_format: str = strftime_by_example("Jan-1")

class IcalModule(PMCard):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._ical = ICalConfig(**config.ical.__dict__)
        self.timer.set_timeout(self._ical.refresh_minutes * 60 * 1000)
        self.ical_response = None
        self.api = PMWebApi(self._ical.url, self._ical.refresh_minutes * 60, self._ical.cache_file)
        self.all_day_format = strftime_by_example(self._ical.all_day_format)
        self.time_format = strftime_by_example(self._ical.time_format)

    def exec(self) -> bool:
        is_dirty = super().exec()
        if not self.timer.is_timedout(): return is_dirty # early exit if not timed out
        self.timer.reset()

        self.ical_response = self.api.fetch_text(blocking=False)
        if not self.ical_response:
            # non-blocking call or error?
            if self.api.error:
                _error(f"Failed to fetch iCalendar data from {self.api.url}: {self.api.error}")
            self.update(
                "iCalendar",
                "(loading...)",
                datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            )
            self.timer.reset(1000)
            return False
        print("got data...")
        # epoch = datetime(1980, 1, 1, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        later = (now + timedelta(hours=24 * self._ical.number_days))
        now_str = now.strftime("%Y-%m-%d")
        later_str = later.strftime("%Y-%m-%d")
        ical_parser = IcalParser(self.ical_response.splitlines())
        events = ical_parser.parse(now_str, later_str)
        event_str = ""
        all_day_str = ""
        event_cnt = 0
        daily_events = []
        all_day_events = []
        for event in events:
            if event_cnt > self._ical.max_events:
                break
            if event.get("dtstart$", "") < now_str:
                continue
            if event.get("all_day"):
                if self._ical.show_all_day_events:
                    all_day_events.append(event)
            else:
                if event.get("rrule", False):
                    if self._ical.show_recurring_events:
                        daily_events.append(event)
                else:
                    if self._ical.show_regular_events:
                        daily_events.append(event)

        for event in daily_events:
            event_str += f"{event.get('dtstart').strftime(self.time_format)}: {event.get('name', event.get('summary', 'none'))}\n"
        for event in all_day_events:
            all_day_str += f"{event.get('dtstart').strftime(self.all_day_format)}: {event.get('name', event.get('summary', 'none'))}\n"
        if self._ical.number_days > 1:
            header_str = f"{self._ical.title}\n{now.strftime(self._ical.title_format)} - {later.strftime(self._ical.title_format)}"
        self.update(
            header_str,
            (event_str + "\n" + all_day_str) or "No Events to Show",
            "last updated\n" + now.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        )
        print("updated...")
        return True # state changed
