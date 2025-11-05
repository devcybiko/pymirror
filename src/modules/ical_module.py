# ical_module.py
# https://openicalmap.org/api/one-call-3#current

from collections import defaultdict
from dataclasses import is_dataclass
from datetime import datetime, timedelta
from arrow import now
from sqlalchemy import extract, and_, func

from pmdb.pmdb import Base
from pymirror.pmcard import PMCard
from utils.utils import json_read, strftime_by_example, to_dict, to_munch, to_naive, to_utc_epoch
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
        self.prev_weeks = self._ical.prev_weeks
        self.rows = self._ical.rows
        self._read_holidays()

    def _read_holidays(self):
        for holiday_file in self._ical.holiday_files:
            holiday_dict = json_read(holiday_file)
            for date, s in holiday_dict.items():
                self.holidays[date].append(s)

    def _date_in(self, now):
        events = []
        dups = set()
        for event in self.all_day_events:
            if now.date() == event.get("dtstart").date():
                if event.summary in dups:
                    continue
                if "Ticket:" in event.summary:
                    ## GLS HACK: skips extra Meetup events
                    continue
                dups.add(event.summary)
                events.append(event)
        for event in self.daily_events:
            if now.date() == event.get("dtstart").date():
                if event.summary in dups:
                    continue
                if "Ticket:" in event.summary:
                    ## GLS HACK: skips extra Meetup events
                    continue
                events.append(event)
        dtstart_st = now.strftime("%Y-%m-%d")
        dtstart_day = now.strftime("%m-%d")
        for holiday in self.holidays[dtstart_st]:
            events.append(holiday)
        for holiday in self.holidays[dtstart_day]:
            events.append(holiday)
        return events

    def _render_header(self, x, y, w, h):
        dow = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for col in range(0, 7):
            if self.days == 5 and (col == 0 or col == 6):
                continue
            self.gfx.text_color = "black"
            self.gfx.text_bg_color = "white"
            self.bitmap.text_box((x, y, x + self.box_width - 1, y + self.header_height - 1), dow[col], halign="center", valign="center", use_baseline=True)
            x += self.box_width
        y += self.header_height
        return x, y

    def _render_holiday_event(self, x, yy, event):
        today = datetime.now().astimezone()
        if event['dtstart'].date() < today.date():
            self.gfx.text_color = "gray"
        else:
            self.gfx.text_color = "#0f0"
        self.gfx.text_bg_color = None
        _, yy = self.bitmap.text_box((x + self.h_padding, yy, x + self.box_width - 1, yy + self.header_height - 1), f"<{event.summary}>", halign="left", valign="top", use_baseline=True)
        yy += self.v_padding
        return yy

    def _render_grid(self, force) -> bool:
        self.bitmap.clear()
        x, y, w, h = self._calc_initial_values()
        x, y = self._render_header(x, y, w, h)
        x = 0
        now = self._calc_start_dates()
        self.h_padding = self.gfx.font.width // 2
        for row in range(0, self.rows):
            self._highlight_this_week(x, y, now)
            for col in range(0, 7):
                events = self._date_in(now)
                if self.days == 5 and (col == 0 or col == 6):
                    now += timedelta(days=1)
                    continue
                line_no = 0
                yy = self._render_date(x, y, self.h_padding, now)
                for event in events:
                    if event['dtstart'].strftime("%H:%M") == "00:00":
                        self._render_holiday_event(x, y, event)
                    else:
                        yy = self._render_event(x, line_no, yy, event)
                        line_no += 1
                self.bitmap.rectangle((x, y, x + self.box_width - 1, y + self.box_height - 1), fill=None)
                x += self.box_width
                now += timedelta(days=1)
            y += self.box_height
            if y + self.box_height > h:
                break
            x = 0
        self.bitmap.gfx_pop()

    def _calc_initial_values(self):
        self.gfx = self.bitmap.gfx_push()
        self.text_colors = ["yellow", "cyan"]
        w = self.bitmap.width
        h = self.bitmap.height
        x = 0
        y = 0
        self.days = self._ical.week_mode
        self.box_width = int(w/self.days) - 1
        self.h_padding = self.gfx.font.width // 2
        self.v_padding = self.gfx.font.height // 2
        self.header_height = self.bitmap.gfx.font.height + 2
        if self._ical.rows:
            self.box_height = int((h - self.header_height) / self._ical.rows)
            self.rows = self._ical.rows
        else:
            self.box_height = int(self.box_width * 3 / 4) ## initial aspect ratio 4:3
            # self.box_height = int(self.box_width * 9 / 16) ## initial aspect ratio 16:9
            self.rows = int((h - self.header_height) / self.box_height)
            self.box_height = int((h - self.header_height) / self.rows) ## recalc to fit exactly
        print(f"ICAL GRID: box_width={self.box_width}, box_height={self.box_height}, days={self.days}")
        return x,y,w,h

    def _render_event(self, x, line_no, yy, event):
        rect = (x + self.h_padding, yy, x + self.box_width - self.h_padding, yy + self.box_height)
        msg = f"{event['dtstart'].strftime(self.time_format)}: {event.get('name', event.get('summary', 'none'))}"
        lines = self.gfx.font.text_split(msg, rect=rect, split="words")
        today = datetime.now().astimezone()
        if event['dtstart'].date() < today.date():
            self.gfx.text_color = "gray"
        else:
            self.gfx.text_color = self.text_colors[line_no % len(self.text_colors)]
        self.gfx.text_bg_color = None
        self.gfx.bg_color = None
        _, yy = self.bitmap.text_box(rect, lines[0:3], halign="left", valign="top", use_baseline=True)
        yy += self.v_padding
        return yy

    def _render_date(self, x, y, padding, date):
        today = datetime.now().astimezone()
        if date.date() < today.date():
            self.gfx.text_color = "gray"
        else:
            self.gfx.text_color = "orange"
        self.gfx.text_bg_color = None
        _, yy = self.bitmap.text_box((x + padding, y, x + self.box_width - padding, y + self.box_height - 1), str(date.month)+"/"+str(date.day), halign="right", valign="top", use_baseline=True)
        yy += self.v_padding
        return yy

    def _highlight_this_week(self, x, y, beginning_of_week):
        today = datetime.now().astimezone()
        if (today.date() - beginning_of_week.date()).days < 0:
            return
        if (today.date() - beginning_of_week.date()).days > 7:
            return
        now = beginning_of_week
        for i in range(0, 7):
            if self.days == 5 and (i == 0 or i == 6):
                now += timedelta(days=1)
                continue
            if now.date() == today.date():
                self.bitmap.rectangle((x, y, x + self.box_width - 1, y + self.box_height - 1), fill="#333")
            # else:
            #     self.bitmap.rectangle((x, y, x + self.box_width - 1, y + self.box_height - 1), fill="#444")
            now += timedelta(days=1)
            x += self.box_width

    def _calc_start_dates(self):
        dow_offset = [1, 2, 3, 4, 5, 6, 0]
        now = datetime.now().astimezone() - timedelta(weeks=self.prev_weeks)
        dow = now.weekday()
        beginning_of_week = now - timedelta(days=dow_offset[dow])
        return beginning_of_week

    def render(self, force: bool) -> bool:
        if self._ical.render_mode == "grid":
            self._render_grid(force)
        else:
            super().render(force)

    def exec(self) -> bool:
        if not self.timer.is_timedout(): 
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._ical.refresh_time)

        now = datetime.now() - timedelta(weeks=self.prev_weeks)
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
            self.daily_events.extend(events)
        all_events = []
        for event in self.daily_events:
            if event.get('dtstart').strftime("%H:%M") == "00:00": continue
            if "Ticket:" in event.summary:
                ## GLS HACK: skips extra Meetup events
                continue

            event_str = f"{event.get('dtstart').strftime(self.time_format)}: {event.get('name', event.get('summary', 'none'))}"
            event.event_str = event_str
            all_events.append(event)
        for event in self.all_day_events:
            if "Ticket:" in event.summary:
                ## GLS HACK: skips extra Meetup events
                continue
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