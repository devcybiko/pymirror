# ical_module.py
# https://openicalmap.org/api/one-call-3#current

from collections import defaultdict
from dataclasses import is_dataclass
from datetime import datetime, timedelta
from sqlalchemy import extract, and_, func

from pmdb.pmdb import Base
from pymirror.pmcard import PMCard
from pymirror.utils.utils import json_read, strftime_by_example, to_dict, to_munch, to_naive, to_utc_epoch
from tasks.ical_task import IcalTable
    
class IcalModule(PMCard):
    def __init__(self, pm, config):
        super().__init__(pm, config)
        self._ical = config.ical
        self.timer.set_timeout(self._ical.refresh_time)
        self.all_day_format = strftime_by_example(self._ical.all_day_format)
        self.time_format = strftime_by_example(self._ical.time_format)
        self.daily_events = []
        self.all_day_events = []
        self.holidays = defaultdict(list)
        self._read_holidays()

    def _read_holidays(self):
        for holiday_file in self._ical.holiday_files:
            holiday_dict = json_read(holiday_file)
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
                        self.bitmap.text_box((x, yy, x + box_width - 1, yy + header_height - 1), f"{event['dtstart'].strftime(self.time_format)}: {event.get('name', event.get('summary', 'none'))}", halign="left", valign="top", use_baseline=True)
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

        now = datetime.now()
        later = (now + timedelta(hours=24 * self._ical.number_days))
        now_epoch = to_utc_epoch(now)
        later_epoch = to_utc_epoch(later)
        self.all_day_events = []
        self.daily_events = []
        if self._ical.show_all_day_events:
            self.all_day_events = to_munch(to_dict(self.pmdb.get_all_where(
                IcalTable, 
                and_(
                    IcalTable.calendar_name == self._ical.calendar_name,
                    IcalTable.utc_start >= now_epoch,
                    IcalTable.utc_end <= later_epoch,
                    IcalTable.all_day == True
                ),
                order_by=IcalTable.utc_start
            )))

        if self._ical.show_regular_events:
            # Check if time is exactly midnight (00:00:00)
            self.daily_events = to_munch(to_dict(self.pmdb.get_all_where(
                IcalTable, 
                and_(
                    IcalTable.calendar_name == self._ical.calendar_name,
                    IcalTable.utc_start >= now_epoch,
                    IcalTable.utc_end <= later_epoch,
                    IcalTable.rrule == "",
                    IcalTable.all_day == False
                ),
                order_by=IcalTable.utc_start
            )))

        if self._ical.show_recurring_events:
            recurring_events = self.pmdb.get_all_where(
                IcalTable, 
                and_(
                    IcalTable.calendar_name == self._ical.calendar_name,
                    IcalTable.utc_start >= now_epoch,
                    IcalTable.utc_end <= later_epoch,
                    IcalTable.rrule != ""
                ),
                order_by=IcalTable.utc_start
            )
            events = [to_munch(to_dict(event)) for event in recurring_events]
            print(157, events)
            self.daily_events.extend(events)
        all_events = []
        for event in self.daily_events:
            print(162, event, isinstance(event, Base))
            event_str = f"{event.get('dtstart').strftime(self.time_format)}: {event.get('name', event.get('summary', 'none'))}"
            event.event_str = event_str
            all_events.append(event)
            print(event.description)
        for event in self.all_day_events:
            if event.description != "\\n":
                ## HACK: holidays in Apple iCal have a "mock" newline
                ## HACK" "regular" events do not
                continue
            all_day_str = f"{event.get('dtstart').strftime(self.all_day_format)}: {event.get('name', event.get('summary', 'none'))}"
            event.event_str = all_day_str
            all_events.append(event)
        events = sorted(all_events, key=lambda e: e.utc_start)
        event_str = "\n".join([event.event_str for event in events])
        if self._ical.number_days > 1:
            header_str = f"{self._ical.title}\n{now.strftime(self._ical.title_format)} - {later.strftime(self._ical.title_format)}"
        self.update(
            header_str,
            (event_str) or "No Events to Show",
            "last updated\n" + now.astimezone().strftime("%Y-%m-%d %H:%M:%S"),
        )
        return True # state changed