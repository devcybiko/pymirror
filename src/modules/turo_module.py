from calendar import month
from datetime import datetime, timedelta
from pydoc import text
from dateutil.relativedelta import relativedelta

import json
from munch import DefaultMunch
from pmdb.pmdb import PMDb
from pymirror.pmmodule import PMModule
from tables.turo_trips_table import TuroTripsTable
from tables.turo_vehicles_table import TuroVehiclesTable
from utils.utils import SafeNamespace

from .turo_calculations import annual_income, monthly_income, annual_sum_of_days

class TuroModule(PMModule):
    def __init__(self, pm, config: SafeNamespace):
        super().__init__(pm, config)
        self._turo = config.turo
        self.timer.set_timeout(self._turo.refresh_time)
        self.database = self._turo.database
        config = DefaultMunch(url="sqlite:///turo.sqlite")
        config.nmonths = 3
        self.turo_db = PMDb(config)
        self.dims = self._compute_dimensions(32)

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
            dims.padding + dims.trip_box_h + \
            (dims.padding + dims.stats_font_size) * 3
        return dims

    def _compute_month_values(self, _month, start_date, end_date, x, y, w, h):
        month = DefaultMunch()
        month.start = datetime(start_date.year, _month, 1)
        month.end = datetime(start_date.year, _month+1, 1) - timedelta(days=1)
        month.days = (month.end - month.start).days + 1
        month.pixels_per_day = w / ((end_date - start_date).days + 1)
        month.x = x + round((month.start - start_date).days * month.pixels_per_day)
        month.y = y
        month.w = month.days * month.pixels_per_day
        month.h = 0
        return month
    
    def _compute_dtrip_values(self, y, month, trip_start=None, trip_end=None):
        dtrip = DefaultMunch()
        dtrip.x = month.x
        dtrip.y = y
        dtrip.h = self.dims.trip_box_h
        dtrip.colors = {
            "Booked": "orange",
            "In-progress": "blue",
            "Completed": "green",
            "Personal": "gray",
            "Dummy": None
        }
        if trip_start and trip_end:
            dtrip.start_days = (trip_start - month.start).days
            dtrip.end_days = (trip_end - month.start).days
            dtrip.x += round(dtrip.start_days * month.pixels_per_day)
            dtrip.w = round((dtrip.end_days - dtrip.start_days) * month.pixels_per_day) - 1
        return dtrip
    
    def _render_personal_trip(self, x, y, month, last_trip, trip):
        gfx = self.bitmap.gfx_push()
        if last_trip is None:
            last_trip = DefaultMunch()
            last_trip.trip_end = month.start
        if trip is None:
            trip = DefaultMunch()
            trip.trip_start = month.end + timedelta(days=1)
        gfx.set_font(None, self.dims.stats_font_size)
        trip_start = last_trip.trip_end
        trip_end = trip.trip_start
        nmins = (trip_end - trip_start).total_seconds() / 60.0
        ndays = float(nmins) / (60.0 * 24.0)
        print(trip_start, trip_end, ndays)
        if ndays > 0.5:
            y += self.dims.earnings_font_size + 1
            dtrip = self._compute_dtrip_values(y, month, trip_start, trip_end)
            personal_trip = trip.copy()
            personal_trip.trip_status = "Personal"
            personal_trip.trip_start = trip_start
            personal_trip.trip_end = trip_end
            personal_trip.trip_days = round(ndays)
            dtrip.y = self._render_trip_days_bar(gfx, dtrip, personal_trip)
        self.bitmap.gfx_pop()
        return y
    
    def _render_today_marker(self, gfx, month, dtrip, box_top):
        today = datetime.now().date()
        if month.start.date() <= today <= month.end.date():
            x = month.x + round((today - month.start.date()).days * month.pixels_per_day)
            self.bitmap.rectangle((x, box_top, x + 4, dtrip.y), fill="red")

    def _create_dummy_trip(self, month):
        dummy_trip = DefaultMunch()
        dummy_trip.trip_status = "Dummy"
        dummy_trip.trip_start = month.start
        dummy_trip.trip_end = month.end
        dummy_trip.total_earnings = 0
        dummy_trip.trip_days = (month.end - month.start).days + 1
        return dummy_trip
    
    def _render_month(self, x, y, w, h, cal_start, cal_end, _month, vehicle_trips, status_list=["Booked", "Completed", "In-progress"]):
        _y = y
        bm = self.bitmap
        gfx = bm.gfx_push()
        month = self._compute_month_values(_month, cal_start, cal_end, x, y, w, h)
        # render month name
        gfx.set_font(None, self.dims.month_font_size)
        _, y = bm.text_box((month.x, y, month.x + month.w, y + self.dims.month_font_size), month.start.strftime("%B"), halign="center", valign="center", use_baseline=True)
        y += self.dims.padding
        last_trip = None
        box_top = y
        dtrip = self._compute_dtrip_values(y, month, month.start, month.end)
        dummy_trip = self._create_dummy_trip(month)
        vehicle_trips = [dummy_trip] + vehicle_trips
        for trip in vehicle_trips:
            trip_start = max(trip.trip_start, month.start)
            trip_end = min(trip.trip_end, month.end)
            if trip.trip_status not in (status_list + ["Dummy"]) \
                 or trip_end <= trip_start \
                 or (trip_start > month.end or trip_end < month.start):
                continue
            self._render_personal_trip(x, y, month, last_trip, trip)
            last_trip = trip
            dtrip = self._compute_dtrip_values(y, month, trip_start, trip_end)
            dtrip.y = self._render_trip_earnings(gfx, month, dtrip, trip, dtrip.start_days, dtrip.end_days)
            dtrip.y = self._render_trip_days_bar(gfx, dtrip, trip)
            dtrip.y = self._render_daily_average(gfx, dtrip, trip)
            dtrip.y = self._render_earnings_per_mile(gfx, dtrip, trip)
            dtrip.y = self._render_vehicle_value(gfx, dtrip, trip)
        # render personal trip at end of month
        self._render_personal_trip(x, y, month, last_trip, None)
        dtrip.y += self.dims.padding
        # render month border
        bm.rectangle((month.x, box_top, month.x + month.w, dtrip.y), outline="white", fill=None)
        self._render_today_marker(gfx, month, dtrip, box_top)
        bm.gfx_pop()
        return box_top, dtrip.y - _y

    def _render_weekend_markers(self, month, box_top, dh):
        bm = self.bitmap
        gfx = bm.gfx_push()
        gfx.color = None
        for day in range((month.end - month.start).days + 1):
            trip_day = month.start + timedelta(days=day)
            if trip_day.weekday() >= 5: # Saturday or Sunday
                x = month.x + round(day * month.pixels_per_day)
                bm.rectangle((x, box_top, x + month.pixels_per_day, month.y + dh), fill="#333", outline=None)
        bm.gfx_pop()

    def _render_earnings_per_mile(self, gfx, dtrip, trip):
        gfx.set_font(None, self.dims.stats_font_size)
        h = gfx.font.height + gfx.font.baseline
        dtrip.y += self.dims.padding
        y = dtrip.y
        try:
            earnings_per_mile = f"${round(trip.total_earnings / trip.distance_traveled, 3)}*{trip.distance_traveled}mi"
            x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + h), f"{earnings_per_mile}", halign="center", valign="center", use_baseline=True)
        except TypeError as e:
            y = dtrip.y + h - 1
        return y

    def _render_daily_average(self, gfx, dtrip, trip):
        dtrip.y += self.dims.padding
        gfx.set_font(None, self.dims.stats_font_size)
        h = gfx.font.height
        daily_average = round(trip.total_earnings / trip.trip_days, 2)
        daily_average = f"${daily_average}/day"
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + h), f"{daily_average}", halign="center", valign="center", use_baseline=True)
        return y

    def _render_vehicle_value(self, gfx, dtrip, trip):
        gfx.set_font(None, self.dims.stats_font_size)
        h = gfx.font.height
        dtrip.y += self.dims.padding
        if not trip.check_out_odometer:
            return dtrip.y + h*4 - 1
        vehicle = self.vehicles[trip.vehicle_nickname]
        depreciation_value = vehicle.last_kbb_value - vehicle.purchase_kbb_value
        depreciation_miles = vehicle.last_mileage - vehicle.purchase_mileage
        depreciation_rate = round(depreciation_value / depreciation_miles, 3) if depreciation_miles != 0 else 0
        delta_miles = trip.check_out_odometer - vehicle.last_mileage
        depreciation_this_trip = round(depreciation_rate * delta_miles, 2)
        current_value = round(vehicle.last_kbb_value + depreciation_this_trip)
        equity = round(current_value - vehicle.remaining_balance)
        gfx.text_color = "white"
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + h), f"${current_value}", halign="center", valign="center", use_baseline=True)
        x, y = self.bitmap.text_box((dtrip.x, y, dtrip.x + dtrip.w, y + h), f"{trip.check_out_odometer}mi", halign="center", valign="center", use_baseline=True)
        x, y = self.bitmap.text_box((dtrip.x, y, dtrip.x + dtrip.w, y + h), f"${depreciation_rate}/mi", halign="center", valign="center", use_baseline=True)
        x, y = self.bitmap.text_box((dtrip.x, y, dtrip.x + dtrip.w, y + h), f"${equity} eqy", halign="center", valign="center", use_baseline=True)
        return y

    def _render_trip_days_bar(self, gfx, dtrip, the_trip):
        dtrip.y += self.dims.padding
        gfx.set_font(None, self.dims.trip_box_font_size)
        self.bitmap.rectangle((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + dtrip.h), fill=dtrip.colors[the_trip.trip_status])
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + dtrip.h), f"{the_trip.trip_days}d")
        return y

    def _render_trip_earnings(self, gfx, month, dtrip, trip, start_days, end_days):
        gfx.set_font(None, self.dims.earnings_font_size)
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + dtrip.h - 1), f"${round(trip.total_earnings)}")
        return y
    
    def _render_vehicle_name(self, x, y, vehicle_name, vehicle_trips):
        _y = y
        gfx = self.bitmap.gfx_push()
        booked_income = round(annual_income(vehicle_trips, ["Booked", "In-progress"]))
        completed_income = round(annual_income(vehicle_trips, ["Completed"]))
        days = annual_sum_of_days(vehicle_trips, ["Booked", "In-progress", "Completed"])
        total_income = booked_income + completed_income
        average_income = round(total_income / days, 2) if days > 0 else 0
        vehicle_name = f"{vehicle_name} - ${str(completed_income)} (${str(booked_income)}) => ${str(total_income)} ({str(days)}d * ${str(average_income)}/day)"
        gfx.set_font(None, self.dims.title_font_size)
        gfx.font.use_bold = True
        self.bitmap.text(vehicle_name, x, y)
        y += gfx.font.height + gfx.font.baseline
        self.bitmap.gfx_pop()
        return y - _y

    def render(self, force: bool) -> bool:
        bm = self.bitmap
        bm.clear()
        bm.gfx.set_font(None, self.dims.title_font_size)
        if not self.trips:
            bm.text("No trips found", 0, 0)
            return True
        x = 0
        y = 0
        w = bm.width
        h = self.dims.month_h
        ## set start_date = january 1st 0f 2026
        total_completed_income = 0
        total_booked_income = 0
        total_days = 0
        for vehicle_name, vehicle_trips in self.trips.items():
            dh = self._render_vehicle_name(x, y, vehicle_name, vehicle_trips)
            y += dh
            cal_start = datetime(datetime.now().year, 1, 1)
            cal_end = cal_start + relativedelta(months=self.config.nmonths) - timedelta(days=1)
            for month in range(1, self.config.nmonths + 1):
                # render once to compute the height of the month block
                box_top, dh = self._render_month(x, y, w, h, cal_start, cal_end, month, vehicle_trips)
                month_data = self._compute_month_values(month, cal_start, cal_end, x, y, w, h)
                self._render_weekend_markers(month_data, box_top, dh)
                self._render_month(x, y, w, h, cal_start, cal_end, month, vehicle_trips)
            y += dh
            total_completed_income += round(annual_income(vehicle_trips, ["Completed"]))
            total_booked_income += round(annual_income(vehicle_trips, ["Booked", "In-progress"]))
            total_days += annual_sum_of_days(vehicle_trips, ["Booked", "In-progress", "Completed"])
            y += self.dims.padding
        total_income = total_completed_income + total_booked_income
        average_income = round(total_income / total_days, 2) if total_days > 0 else 0
        bm.gfx.set_font(None, self.dims.title_font_size)
        bm.text(f"Total: ${str(total_completed_income)} (${str(total_booked_income)}) => ${str(total_income)} ({str(total_days)}d * ${str(average_income)}/day)", x, y)        
        return True

    def exec(self) -> bool:
        if not self.timer.is_timedout(): 
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._turo.refresh_time)
        rows = self.turo_db.get_all(TuroTripsTable)
        rows = sorted(rows, key=lambda x: x.trip_end)
        self.trips = DefaultMunch()
        for row in rows:
            trip = DefaultMunch.fromDict(row.__dict__)
            if self.trips[trip.vehicle_nickname] is None:
                self.trips[trip.vehicle_nickname] = []
            self.trips[trip.vehicle_nickname].append(DefaultMunch.fromDict(trip.__dict__))
        rows = self.turo_db.get_all(TuroVehiclesTable)
        rows = sorted(rows, key=lambda x: x.vehicle_id)
        self.vehicles = DefaultMunch()
        for row in rows:
            vehicle = DefaultMunch.fromDict(row.__dict__)
            self.vehicles[vehicle.nickname] = DefaultMunch.fromDict(vehicle.__dict__)
        return True # state changed