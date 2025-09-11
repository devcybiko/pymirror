# ical_module.py
# https://openicalmap.org/api/one-call-3#current

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
import json
import time
from ics import Calendar

from pymirror.pmcard import PMCard
from pymirror.pmwebapi import PMWebApi
from pymirror.utils import SafeNamespace, strftime_by_example, to_int
from pymirror.pmlogger import _debug, _error
from pymirror.ical_parser import IcalParser

@dataclass
class ICalConfig:
    url: str = None
    title: str = "iCalendar"
    cache_file: str = "./caches/ical.json"
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
    row_height: int = None
    rows: int = 1000
    holiday_files: list = field(default_factory=list)
    
class IcalModule(PMCard):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._ical = ICalConfig(**config.ical.__dict__)
        self.timer.set_timeout(self._ical.refresh_time)
        self.ical_response = None
        self.api = PMWebApi(self._ical.url, self._ical.refresh_time * 60, self._ical.cache_file)
        self.all_day_format = strftime_by_example(self._ical.all_day_format)
        self.time_format = strftime_by_example(self._ical.time_format)
        self.daily_events = []
        self.all_day_events = []
        self.holidays = defaultdict(list)
        self._read_holidays()

    def _read_holidays(self):
        for holiday_file in self._ical.holiday_files:
            with open(holiday_file) as f:
                holiday_dict = json.load(f)
            for date, s in holiday_dict.items():
                self.holidays[date].append(s)

    def _date_in(self, now):
        events = []
        for event in self.daily_events:
            if now.date() == event.get("dtstart").date():
                events.append(event)
        dtstart_st = now.strftime("%Y-%m-%d")
        dtstart_day = now.strftime("%m-%d")
        for holiday in self.holidays[dtstart_st]:
            events.append(holiday)
        for holiday in self.holidays[dtstart_day]:
            events.append(holiday)
        return events

    def render_grid(self, force) -> bool:
        w = self.bitmap.width
        h = self.bitmap.height
        x = 0
        y = 0
        days = self._ical.week_mode
        box_width = int(w/days) - 1
        header_height = self.bitmap.gfx.font.height + 2
        dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        gfx = self.bitmap.gfx_push()
        gfx.text_color, gfx.text_bg_color = gfx.text_bg_color, gfx.text_color
        gfx.bg_color = None
        for col in range(0, 7):
            if days == 5 and (col == 0 or col == 6):
                continue
            self.bitmap.text_box((x, y, x + box_width - 1, y + header_height - 1), dow[col], halign="center", valign="center", use_baseline=True)
            x += box_width
        y += header_height
        if self._ical.row_height == None:
            box_height = box_width // 2
        elif self._ical.row_height == 0:
            box_height = int(h / self._ical.rows)
        else:
            box_height = self._ical.row_height
        x = 0
        now = datetime.now().astimezone()
        today = now
        dow_offset = [1, 2, 3, 4, 5, 6, 0]
        dow = now.weekday()
        then = now - timedelta(days=dow_offset[dow])
        now = then
        text_color, text_bg_color = "yellow", gfx.text_color
        for row in range(0, self._ical.rows):
            for col in range(0, 7):
                gfx.text_color = text_color
                gfx.text_bg_color = text_bg_color
                if now.date() == today.date():
                    gfx.text_bg_color = "#444"
                events = self._date_in(now)
                date = now
                now += timedelta(hours=24)
                if days == 5 and (col == 0 or col == 6):
                    continue

                self.bitmap.text_box((x, y, x + box_width - 1, y + box_height - 1), str(date.month)+"/"+str(date.day), halign="right", valign="top", use_baseline=True)
                yy = y + header_height
                for event in events:
                    if type(event) is str:
                        # holiday
                        self.bitmap.gfx.text_color = "cyan"
                        self.bitmap.text_box((x, yy, x + box_width - 1, yy + header_height - 1), f"{event}", halign="left", valign="top", use_baseline=True)                 
                    else:
                        self.bitmap.gfx.text_color = text_color
                        self.bitmap.text_box((x, yy, x + box_width - 1, yy + header_height - 1), f"{event['dtstart'].hour}:{event['dtstart'].minute:02d}: {event.get('name', event.get('summary', 'none'))}", halign="left", valign="top", use_baseline=True)
                    yy += header_height
                self.bitmap.rectangle((x, y, x + box_width - 1, y + box_height - 1))
                x += box_width
            y += box_height
            if y + box_height > h:
                break
            x = 0
        self.bitmap.gfx_pop()

    def render(self, force: bool) -> bool:
        if self._ical.render_mode == "grid":
            self.render_grid(force)
        else:
            super().render(force)

    def exec(self) -> bool:
        if not self.timer.is_timedout(): 
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._ical.refresh_time)

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
            # wait 1 second and check again
            self.timer.reset(1000)
            # render the display in the interim
            return True
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

        self.daily_events = daily_events
        self.all_day_events = all_day_events
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
        return True # state changed
