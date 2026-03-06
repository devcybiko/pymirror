from calendar import month
from datetime import datetime, timedelta
from pydoc import text
from dateutil.relativedelta import relativedelta

import json
from munch import DefaultMunch
from configs.turo_trip_config import TuroTripConfig
from pmdb.pmdb import PMDb
from pymirror.pmmodule import PMModule
from tables.turo_trips_table import TuroTripsTable
from tables.turo_vehicles_table import TuroVehiclesTable
from utils.utils import SafeNamespace

from .turo_calculations import annual_income, annual_sum_of_days

class TuroTripModule(PMModule):
    def __init__(self, pm, config: SafeNamespace):
        super().__init__(pm, config)
        self._trip: TuroTripConfig = config.turo_trip
        self.timer.set_timeout(self._trip.refresh_time)
        self.database = self._trip.database
        config = DefaultMunch(url="sqlite:///turo.sqlite")
        self.turo_db = PMDb(config)
        self.dims = self._compute_dimensions(32)
        self.nmonths = self._trip.nmonths
        self.cal = self._compute_cal_values()

    def _compute_cal_values(self):
        cal = DefaultMunch()
        cal.start = datetime.strptime(self._trip.start_date, "%Y-%m-%d")
        cal.end = cal.start + relativedelta(months=self.nmonths) - timedelta(days=1)
        cal.days = (cal.end - cal.start).days + 1
        cal.pixels_per_day = self.bitmap.width / cal.days
        return cal
    
    def _compute_dimensions(self, title_font_size: int = 32):
        dims = DefaultMunch()
        dims.padding = 4
        dims.title_font_size = title_font_size
        dims.month_font_size = 16
        dims.earnings_font_size = 16
        dims.stats_font_size = 12
        dims.trip_box_font_size = 12
        dims.trip_box_h = dims.trip_box_font_size + dims.padding * 2
        dims.month_h = \
            dims.padding + dims.month_font_size + \
            dims.padding + dims.earnings_font_size + \
            dims.padding + dims.trip_box_h
        return dims

    def _compute_month_box(self, month_n, x, y, w, h):
        cal = self.cal
        box = DefaultMunch()
        box.start = cal.start + relativedelta(months=month_n)
        box.end = box.start + relativedelta(months=1) - relativedelta(days=1)
        box.days = (box.end - box.start).days + 1
        box.pixels_per_day = self.cal.pixels_per_day
        box.x = int(x + round((box.start - cal.start).days * cal.pixels_per_day))
        box.y = y
        box.w = int(box.days * cal.pixels_per_day)
        box.h = h
        return box
    
    def _compute_trip_bar(self, y, month, trip_start=None, trip_end=None):
        bar = DefaultMunch()
        bar.x = 0
        bar.y = y
        bar.h = self.dims.trip_box_h
        bar.colors = {
            "Booked": "orange",
            "In-progress": "blue",
            "Completed": "green",
            "Personal": "gray",
            "Dummy": None
        }
        if trip_start and trip_end:
            bar.start_days = (trip_start - self.cal.start).days
            bar.end_days = (trip_end - self.cal.start).days
            bar.x += round(bar.start_days * month.pixels_per_day)
            bar.w = round((bar.end_days - bar.start_days) * month.pixels_per_day) - 1
        return bar
        
    def _render_today_marker(self, gfx, month, dtrip, box_top):
        today = datetime.now().date()
        if month.start.date() <= today <= month.end.date():
            x = month.x + round((today - month.start.date()).days * month.pixels_per_day)
            self.bitmap.rectangle((x, box_top, x + 4, dtrip.y), fill="red")

    def _render_weekend_markers(self, box):
        bm, gfx = self._gfx_push()
        gfx.fill_color = "#333"
        gfx.color = "#333"
        for day in range((box.end - box.start).days + 1):
            trip_day = box.start + timedelta(days=day)
            if trip_day.weekday() >= 5: # Saturday or Sunday
                x = box.x + round(day * box.pixels_per_day)
                y = box.y
                w = round(box.pixels_per_day)
                h = box.h
                _x, _y = bm.rectangle((x, y, x+w, y+h), fill="#333", outline=None)
        self._gfx_pop()
        return _x, _y

    def _render_trip_days_bar(self, gfx, y, bar, the_trip):
        y += self.dims.padding
        gfx.set_font(None, self.dims.trip_box_font_size)
        self.bitmap.rectangle((bar.x, y, bar.x + bar.w, y + bar.h), fill=bar.colors[the_trip.trip_status])
        x, y = self.bitmap.text_box((bar.x, y, bar.x + bar.w, y + bar.h), f"{the_trip.trip_days}d")
        return x, y

    def _render_trip_earnings(self, gfx, y, box, bar, trip):
        gfx.set_font(None, self.dims.earnings_font_size)
        y += self.dims.padding * 2
        x, y = self.bitmap.text_box((bar.x, y, bar.x + bar.w, y + bar.h - 1), f"${round(trip.total_earnings)}")
        return x, y

    def _render_trip(self, x, y, month_n, vehicle, vehicle_trips, status_list):
        bm, gfx = self._gfx_push()
        w, h = bm.width, self.dims.month_h
        box = self._compute_month_box(month_n, x, y, w, h)
        bar = self._compute_trip_bar(y, box, box.start, box.end)
        _x, _y = (x, y)
        for trip in vehicle_trips:
            trip_start = trip.trip_start
            trip_end = trip.trip_end
            if trip.trip_status not in (status_list + ["Dummy"]): continue # its not an interesting trip
            if trip_end <= trip_start: continue # might happen if we use the min/max values
            if (trip_start > box.end) or (trip_end < box.start): continue # if the trip is not within the month boundary
            bar = self._compute_trip_bar(y, box, trip_start, trip_end)
            _x, y0 = self._render_trip_earnings(gfx, y, box, bar, trip)
            _x, _y = self._render_trip_days_bar(gfx, y0, bar, trip)
        bar.y += self.dims.padding
        self._gfx_pop()
        return _x, _y

    def _render_trips(self, x, y, vehicle, vehicle_trips, status_list=["Booked", "Completed", "In-progress"]):
        _x, _y = (0, 0)
        for month_n in range(0, self.nmonths):
            _x, _y = self._render_trip(x, y, month_n, vehicle, vehicle_trips, status_list)
        return _x, _y

    def _render_vehicle_name(self, x, y, vehicle_name, vehicle_trips):
        gfx = self.bitmap.gfx_push()
        booked_income = round(annual_income(vehicle_trips, ["Booked", "In-progress"]))
        completed_income = round(annual_income(vehicle_trips, ["Completed"]))
        days = annual_sum_of_days(vehicle_trips, ["Booked", "In-progress", "Completed"])
        total_income = booked_income + completed_income
        average_income = round(total_income / days, 2) if days > 0 else 0
        vehicle_name = f"{vehicle_name} - ${str(completed_income)} (${str(booked_income)}) => ${str(total_income)} ({str(days)}d * ${str(average_income)}/day)"
        gfx.set_font(None, self.dims.title_font_size)
        gfx.font.use_bold = True
        self.bitmap.text_box((x, y, self.bitmap.width, y + self.dims.title_font_size), vehicle_name, halign="left", valign="center", use_baseline=True)
        y += gfx.font.height + gfx.font.baseline
        self.bitmap.gfx_pop()
        return x, y

    def _render_month_box(self, x, y, month_n):
        bm, gfx = self._gfx_push()
        w, h = bm.width, self.dims.month_h
        box = self._compute_month_box(month_n, x, y, w, h)
        box.y += self.dims.padding
        self._render_weekend_markers(box)
        _x, _y = bm.rectangle((box.x, box.y, box.x + box.w, box.y + box.h), fill=None)
        self._gfx_pop()
        return _x, _y

    def _render_month_name(self, x, y, month_n):
        bm, gfx = self._gfx_push()
        w, h = bm.width, self.dims.month_h
        box = self._compute_month_box(month_n, x, y, w, h)
        box.y += self.dims.padding*2
        _x, _y = bm.text_box((box.x, box.y, box.x + box.w, box.y + self.dims.month_font_size), box.start.strftime("%B %Y"), halign="center", valign="center", use_baseline=True)
        self._gfx_pop()
        return _x, _y

    def _render_month_names(self, x, y, vehicle, vehicle_trips):
        for month_n in range(0, self.nmonths):
            _x, _y = self._render_month_name(x, y, month_n)
        return _x, _y

    def _render_month_boxes(self, x, y, vehicle, vehicle_trips):
        for month_n in range(0, self.nmonths):
            _x, _y = self._render_month_box(x, y, month_n)
        return _x, _y

    def render(self, force: bool) -> bool:
        bm = self.bitmap
        gfx = bm.gfx_push()
        bm.clear()
        gfx.set_font(None, self.dims.title_font_size)
        if not self.trips:
            bm.text("No trips found", 0, 0)
            return True
        (x, y) = (0, 0)
        _y = y
        for vehicle_nickname, vehicle_trips in self.trips.items():
            vehicle = self.vehicles[vehicle_nickname]
            _, y0 = self._render_vehicle_name(x, y, vehicle.nickname, vehicle_trips)
            _, y1 = self._render_month_names(x, y0, vehicle, vehicle_trips)
            _, y2 = self._render_month_boxes(x, y1, vehicle, vehicle_trips)
            _, y3 = self._render_trips(x, y1, vehicle, vehicle_trips)
            y = y2 + self.dims.padding*2
        
        return True

    def exec(self) -> bool:
        if not self.timer.is_timedout(): 
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._trip.refresh_time)
        rows = self.turo_db.get_all_where(TuroTripsTable, f"vehicle_nickname='{self._trip.vehicle_nickname}'")
        self.trips = DefaultMunch()
        for row in rows:
            trip = DefaultMunch.fromDict(row.__dict__)
            self.trips.setdefault(trip.vehicle_nickname, []).append(trip)
        rows = self.turo_db.get_all_where(TuroVehiclesTable, f"nickname='{self._trip.vehicle_nickname}'")
        rows = sorted(rows, key=lambda x: x.vehicle_id)
        self.vehicles = DefaultMunch()
        for row in rows:
            vehicle = DefaultMunch.fromDict(row.__dict__)
            self.vehicles[vehicle.nickname] = vehicle
        return True # state changed