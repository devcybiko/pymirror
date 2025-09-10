# ical_module.py
# https://openicalmap.org/api/one-call-3#current

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import time
from ics import Calendar, Event

from pymirror.ical_parser import IcalParser
from pymirror.pmcard import PMCard
from pymirror.pmmodule import PMModule
from pymirror.pmwebapi import PMWebApi
from pymirror.utils import SafeNamespace, strftime_by_example
from pymirror.pmlogger import _debug, _error

@dataclass
class ICalConfig:
    url: str = None
    cache_file: str = "./caches/ical2.json"
    refresh_minutes: int = 60
    max_events: int = 10
    number_days: int = 7
    time_format: str = strftime_by_example("0:00 PM")
    show_all_day_events: bool = True
    show_recurring_events: bool = True
    all_day_format: str = strftime_by_example("Jan-1")

class Ical2Module(PMModule):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._ical2 = ICalConfig(**config.ical2.__dict__)
        self.timer.set_timeout(self._ical2.refresh_minutes * 60 * 1000)
        self.ical_response = None
        self.api = PMWebApi(self._ical2.url, self._ical2.refresh_minutes * 60, self._ical2.cache_file)
        self.all_day_format = strftime_by_example(self._ical2.all_day_format)
        self.time_format = strftime_by_example(self._ical2.time_format)

    def _date_in(self, now):
        events = []
        for event in self.daily_events:
            if now.date() == event.get("dtstart").date():
                events.append(event)
        return events

    def render(self, force) -> bool:
        w = self.bitmap.width
        h = self.bitmap.height
        x = 0
        y = 0
        dx = int(w/7) - 1
        dh = self.bitmap.gfx.font.height + 2
        dy = dh
        dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        gfx = self.bitmap.gfx_push()
        gfx.text_color, gfx.text_bg_color = gfx.text_bg_color, gfx.text_color
        gfx.bg_color = None
        for col in range(0, 7):
            self.bitmap.text_box((x, y, x + dx - 1, y + dy - 1), dow[col], halign="center", valign="center", use_baseline=True)
            x += dx
        y += dy
        dy = dx
        x = 0
        now = datetime.now()
        dow_offset = [1, 2, 3, 4, 5, 6, 0]
        dow = now.weekday()
        now -= timedelta(days=dow_offset[dow])
        gfx.text_color, gfx.text_bg_color = "yellow", gfx.text_color
        for row in range(0, 4):
            for col in range(0, 7):
                self.bitmap.text_box((x, y, x + dx - 1, y + dy - 1), str(now.month)+"/"+str(now.day), halign="right", valign="top", use_baseline=True)
                events = self._date_in(now)
                yy = y + dh
                for event in events:
                    self.bitmap.text_box((x, yy, x + dx - 1, yy + dh - 1), f"{event['dtstart'].hour}:{event['dtstart'].minute:02d}", halign="left", valign="top", use_baseline=True)
                    yy += dh
                    self.bitmap.text_box((x, yy, x + dx - 1, yy + dh - 1), f"  {event.get('name', event.get('summary', 'none'))}", halign="left", valign="top", use_baseline=True)
                    yy += dh
                self.bitmap.rectangle((x, y, x + dx - 1, y + dy - 1))
                now += timedelta(hours=24)
                x += dx
            y += dy
            x = 0


    def exec(self) -> bool:
        is_dirty = super().exec()
        if not self.timer.is_timedout(): return is_dirty # early exit if not timed out
        self.timer.reset()

        self.ical_response = self.api.fetch_text(blocking=True)
        print("got data...")
        now = datetime.now(timezone.utc)
        later = now + timedelta(hours=24 * self._ical2.number_days)
        now_str = now.strftime("%Y-%m-%d")
        later_str = later.strftime("%Y-%m-%d")
        ical_parser = IcalParser(self.ical_response.splitlines())
        events = ical_parser.parse(now_str, later_str)
        
        event_cnt = 0
        daily_events = []
        all_day_events = []
        for event in events:
            if event_cnt > self._ical2.max_events:
                break
            if event["dtstart"] < now:
                continue
            if event["all_day"] and self._ical2.show_all_day_events:
                all_day_events.append(event)
            else:
                if event.get("rrule", False):
                    if self._ical2.show_recurring_events:
                        daily_events.append(event)
                else:
                    daily_events.append(event)
        self.daily_events = daily_events
        self.all_day_events = all_day_events
        return True # state changed
