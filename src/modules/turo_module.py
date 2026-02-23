from calendar import month
from datetime import datetime, timedelta
from pydoc import text
from dateutil.relativedelta import relativedelta

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
        self.turo_db = PMDb(config)
        self.dims = self._compute_dimensions(32)

    def _compute_dimensions(self, title_font_size: int = 32):
        dims = DefaultMunch()
        dims.padding = 4
        dims.title_font_size = title_font_size
        dims.month_font_size = 16
        dims.earnings_font_size = 16
        dims.stats_font_size = 12
        dims.earnings_h = round(dims.stats_font_size * 1.5)
        dims.trip_box_font_size = 12
        dims.trip_box_h = dims.trip_box_font_size + dims.padding * 2
        dims.month_h = \
            dims.padding + dims.month_font_size + \
            dims.padding + dims.earnings_h + \
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
        month.y = y + self.dims.padding
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
            "Completed": "green"
        }
        if trip_start and trip_end:
            dtrip.start_days = (trip_start - month.start).days
            dtrip.end_days = (trip_end - month.start).days
        return dtrip
    
    def _render_month(self, x, y, w, h, start_date, end_date, _month, vehicle_trips, status_list=["Booked", "Completed", "In-progress"]):
        _y = y
        gfx = self.bitmap.gfx_push()
        y += self.dims.padding
        month = self._compute_month_values(_month, start_date, end_date, x, y, w, h)
        dtrip = self._compute_dtrip_values(y, month)
        for trip in vehicle_trips:
            trip_start = max(trip.trip_start, month.start)
            trip_end = min(trip.trip_end, month.end)
            if trip.trip_status not in status_list \
                 or trip_end <= trip_start \
                 or (trip_start > month.end or trip_end < month.start):
                continue
            dtrip = self._compute_dtrip_values(y, month, trip_start, trip_end)
            dtrip.y = self._render_trip_earnings(gfx, month, dtrip, trip, dtrip.start_days, dtrip.end_days)
            dtrip.y = self._render_trip_days_bar(gfx, dtrip, trip)
            dtrip.y = self._render_daily_average(gfx, dtrip, trip)
            dtrip.y = self._render_earnings_per_mile(gfx, dtrip, trip)
            dtrip.y = self._render_vehicle_value(gfx, dtrip, trip)
        dtrip.y += self.dims.padding
        self.bitmap.rectangle((month.x, _y, month.x + month.w, dtrip.y), outline="white", fill=None)
        self.bitmap.gfx_pop()
        return dtrip.y - _y

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
        h = gfx.font.height + gfx.font.baseline
        daily_average = round(trip.total_earnings / trip.trip_days, 2)
        daily_average = f"${daily_average}/day"
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + h), f"{daily_average}", halign="center", valign="center", use_baseline=True)
        return y

    def _render_vehicle_value(self, gfx, dtrip, trip):
        gfx.set_font(None, self.dims.stats_font_size)
        h = gfx.font.height + gfx.font.baseline
        dtrip.y += self.dims.padding
        if not trip.check_out_odometer:
            return dtrip.y + h - 1
        vehicle = self.vehicles[trip.vehicle_nickname]
        delta_value = vehicle.purchase_value - vehicle.last_value
        delta_miles = vehicle.purchase_mileage - vehicle.last_mileage
        depreciation_rate = -round(delta_value / delta_miles, 3) if delta_miles != 0 else 0
        current_value = round(vehicle.purchase_value - depreciation_rate * (trip.check_out_odometer - vehicle.purchase_mileage))
        gfx.text_color = "white"
        print(f"delta_value: {delta_value}, delta_miles: {delta_miles}, depreciation_rate: {depreciation_rate}, current_value: {current_value}")
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + h), f"${current_value} @ ${depreciation_rate}/mi", halign="center", valign="center", use_baseline=True)
        return y

    def _render_trip_days_bar(self, gfx, dtrip, trip):
        dtrip.y += self.dims.padding
        gfx.set_font(None, self.dims.trip_box_font_size)
        self.bitmap.rectangle((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + dtrip.h), fill=dtrip.colors[trip.trip_status])
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + dtrip.h), f"{trip.trip_days}d")
        return y

    def _render_trip_earnings(self, gfx, month, dtrip, trip, start_days, end_days):
        dtrip.x += round(start_days * month.pixels_per_day)
        dtrip.w = round((end_days - start_days) * month.pixels_per_day) - 1
        dtrip.h = self.dims.earnings_font_size - 1
        gfx.set_font(None, self.dims.earnings_font_size)
            # total earnings for the trip
        x, y = self.bitmap.text_box((dtrip.x, dtrip.y, dtrip.x + dtrip.w, dtrip.y + dtrip.h), f"${round(trip.total_earnings)}")
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
        self.bitmap.clear()
        self.bitmap.gfx.set_font(None, self.dims.title_font_size)
        if not self.trips:
            self.bitmap.text("No trips found", 0, 0)
            return True
        x = 0
        y = 0
        w = self.bitmap.width
        h = self.dims.month_h
        nmonths = 3
        ## set start_date = january 1st 0f 2026
        total_completed_income = 0
        total_booked_income = 0
        total_days = 0
        for vehicle_name, vehicle_trips in self.trips.items():
            dh = self._render_vehicle_name(x, y, vehicle_name, vehicle_trips)
            y += dh
            cal_start = datetime(datetime.now().year, 1, 1)
            cal_end = cal_start + relativedelta(months=nmonths) - timedelta(days=1)
            for month in range(1, nmonths + 1):
                dh = self._render_month(x, y, w, h, cal_start, cal_end, month, vehicle_trips)
            y += dh
            total_completed_income += round(annual_income(vehicle_trips, ["Completed"]))
            total_booked_income += round(annual_income(vehicle_trips, ["Booked", "In-progress"]))
            total_days += annual_sum_of_days(vehicle_trips, ["Booked", "In-progress", "Completed"])
        total_income = total_completed_income + total_booked_income
        average_income = round(total_income / total_days, 2) if total_days > 0 else 0
        self.bitmap.text(f"Total: ${str(total_completed_income)} (${str(total_booked_income)}) => ${str(total_income)} ({str(total_days)}d * ${str(average_income)}/day)", x, y)        
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