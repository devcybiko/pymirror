from datetime import datetime, timedelta
import sys            
from dateutil.relativedelta import relativedelta

from flask import json
from munch import DefaultMunch
from sqlalchemy import Table, MetaData
from pmdb.pmdb import PMDb
from pymirror.pmmodule import PMModule
from tables.turo_trips_table import TuroTripsTable
from tables.turo_vehicles_table import TuroVehiclesTable
from utils.utils import SafeNamespace

class TuroModule(PMModule):
    def __init__(self, pm, config: SafeNamespace):
        super().__init__(pm, config)
        self._turo = config.turo
        self.timer.set_timeout(self._turo.refresh_time)
        self.database = self._turo.database
        config = DefaultMunch(url="sqlite:///turo.sqlite")
        self.turo_db = PMDb(config)
        self.dims = self._compute_dimensions(32)

    def _annual_income(self, trips, status_list=["Booked", "Completed", "In-progress"]):
        total = 0
        for trip in trips:
            if trip.trip_status in status_list:
                total += trip.total_earnings
        return total

    def _monthly_income(self, trips, month, status_list=["Booked", "Completed", "In-progress"]):
        total = 0
        for trip in trips:
            if trip.trip_status not in status_list:
                continue
            if trip.trip_end.month == month:
                total += trip.total_earnings
        return total
    
    def _annual_sum_of_days(self, trips, status_list=["Booked", "Completed", "In-progress"]):
        total = 0
        for trip in trips:
            if trip.trip_status not in status_list:
                continue
            total += trip.trip_days
        return total

    def _render_vehicle_value(self, x, y, h, trip, dx0, dx1, dh):
        vehicle = self.vehicles[trip.vehicle_nickname]
        delta_value = vehicle.purchase_value - vehicle.last_value
        delta_miles = vehicle.purchase_mileage - vehicle.last_mileage
        depreciation_rate = -round(delta_value / delta_miles, 3) if delta_miles != 0 else 0
        current_value = round(vehicle.purchase_value - depreciation_rate * (trip.check_out_odometer - vehicle.purchase_mileage))
        self.bitmap.gfx.text_color = "white"
        print(f"delta_value: {delta_value}, delta_miles: {delta_miles}, depreciation_rate: {depreciation_rate}, current_value: {current_value}")
        self.bitmap.text_box((x+dx0-40, y+dh*9, x+dx1+40, y+dh*11), f"${current_value} @ ${depreciation_rate}/mi", halign="center", valign="center", use_baseline=True)

    def _render_earnings_per_mile(self, x, y, h, trip, dx0, dx1, dh):
        try:
            earnings_per_mile = f"${round(trip.total_earnings / trip.distance_traveled, 3)}*{trip.distance_traveled}mi"
        except TypeError as e:
            earnings_per_mile = ""
        self.bitmap.text_box((x+dx0-40, y+dh*7, x+dx1+40, y+h), f"{earnings_per_mile}", halign="center", valign="center", use_baseline=True)

    def _render_daily_average(self, x, y, trip, dx0, dx1, dh):
        daily_average = round(trip.total_earnings / trip.trip_days, 2)
        daily_average = f"${daily_average}/day"
        self.bitmap.text_box((x+dx0-40, y+dh*5+2, x+dx1+40, y+dh*6), f"{daily_average}", halign="center", valign="center", use_baseline=True)

    def _render_trip_days_box(self, x, y, trip, dx0, dx1, dy0, dy1):
        self.bitmap.gfx.text_color = "white"
        self.bitmap.gfx.set_font(None, self.bitmap.gfx.font.height-4)
        self.bitmap.text_box((x+dx0, y + dy0, x+dx1, y+dy1), f"{str(round(trip.trip_days))}d", halign="center", valign="center", use_baseline=True)

    def _render_trip_box(self, x, y, w, h, trip, nmonths, trip_start, trip_end, status_color_map):
        dx0, dx1, dy0, dy1, dh = self._compute_box_dimensions(w, h, nmonths, trip_start, trip_end)
        y -= dh
        trip_color = status_color_map[trip.trip_status]
        self.bitmap.rectangle((x+dx0, y+dy0, x+dx1, y+dy1), fill=trip_color)
        self._render_trip_days_box(x, y, trip, dx0, dx1, dy0, dy1)
        return y,dx0,dx1,dy0,dy1,dh

    def _compute_dimensions(self, title_font_size: int = 32):
        dims = DefaultMunch()
        dims.title_font_size = title_font_size
        dims.month_font_size = 16
        dims.earnings_font_size = 16
        dims.stats_font_size = 12
        dims.earnings_h = round(dims.stats_font_size * 1.5)
        dims.trip_h = dims.earnings_font_size
        dims.padding = 4
        dims.month_h = \
            dims.padding + dims.month_font_size + \
            dims.padding + dims.earnings_h + \
            dims.padding + dims.trip_h + \
            (dims.padding + dims.stats_font_size) * 3
        return dims
    
    def _next_trip(self, trips, n, status_list=["Booked", "Completed", "In-progress"]):
        for next_n in range(n+1, len(trips)):
            if trips[next_n].trip_status in status_list:
                return trips[next_n]
        return DefaultMunch(trip_start=datetime(datetime.now().year, 12, 31), trip_end=datetime(datetime.now().year, 12, 31))

    def _render_personal(self, x, y, w, h, n, trips, start_month, nmonths, i, status_list=["Booked", "Completed", "In-progress"]):
        if n + 1 >= len(trips) \
            or trips[n].trip_status not in status_list:
                return i
        this_trip = trips[n]
        next_trip = self._next_trip(trips, n, status_list)
        trip_start = this_trip.trip_end
        trip_end = next_trip.trip_start
        if trip_end - trip_start < timedelta(days=1) \
            or trip_end < datetime(datetime.now().year, start_month, 1) \
            or trip_end.year != datetime.now().year \
            or trip_start.month < start_month \
            or trip_start.month >= start_month + nmonths:
                return i
        self.bitmap.gfx_push()
        trip_color = None
        self.bitmap.rectangle((x+dx0, y + dy0, x+dx1, y+dy1), fill=trip_color)
        miles = ""
        try:
            miles = " / " + str(next_trip.check_in_odometer - this_trip.check_out_odometer) + "mi"
        except TypeError as e:
            ## ignore if check_in_odometer or check_out_odometer is None or spaces
            pass
        days = (trip_end - trip_start).days
        self.bitmap.text_box((x+dx0, y + h/2 - dh, x+dx1, y+h/2 + dh), f"{days}d{miles}", halign="center", valign="center", use_baseline=True)
        self.bitmap.gfx.set_font(None, 0.20)
        self.bitmap.gfx_pop()
        return i

    def _render_trip(self, x, y, w, h, trip, start_month, nmonths, i, status_list=["Booked", "Completed", "In-progress"]):
        trip_start = trip.trip_start
        trip_end = trip.trip_end
        if trip.trip_status not in status_list \
            or trip_end < datetime(datetime.now().year, start_month, 1) \
            or trip_start > datetime(datetime.now().year, start_month + nmonths, 1) \
            or trip_start.month < start_month \
            or trip_start.month >= start_month + nmonths:
                return i
        self.bitmap.gfx_push()
        status_color_map = DefaultMunch("gray", {
            "Booked": "gray",
            "In-progress": "blue",
            "Completed": "green"
        })
        y, dx0, dx1, dy0, dy1, dh = self._render_trip_box(x, y, w, h, trip, nmonths, trip_start, trip_end, status_color_map)
        self._render_trip_days_box(x, y, trip, dx0, dx1, dy0, dy1)
        self._render_daily_average(x, y, trip, dx0, dx1, dh)
        self._render_earnings_per_mile(x, y, h, trip, dx0, dx1, dh)
        if trip.trip_status == "Completed":
            self._render_vehicle_value(x, y, h, trip, dx0, dx1, dh)
        i += 1
        self.bitmap.gfx_pop()
        return i

    def _render_trips(self, y, w, h, vehicle_name, trips, start_month, nmonths, top_bottom):
        self.bitmap.gfx_push()
        self.bitmap.gfx.set_font(None, self.dims.earnings_font_size)
        _y = y
        x = 0
        i = 0
        if top_bottom == "top":
            y += self.dims.padding
        self._render_weekend_markers(x, y, w, h, trips, start_month, nmonths, top_bottom)
        # for n, trip in enumerate(trips):
            # ...
            # i = self._render_trip(x, y, w, h, trip, start_month, nmonths, i, ["Booked", "Completed", "In-progress"])
            # i = self._render_personal(x, y, w, h, n, trips, start_month, nmonths, i, ["Booked", "Completed", "In-progress"])
        # self._render_today_marker(y, w, h, start_month, nmonths)
        y += h
        if top_bottom == "bottom":
            y += self.bitmap.gfx.font.height + self.bitmap.gfx.font.baseline
        self.bitmap.gfx_pop()
        return y - _y

    def _render_month_names(self, x, y, w, h, trips, start_month, nmonths, top_bottom):
        self.bitmap.gfx_push()
        self.bitmap.gfx.set_font(None, self.dims.month_font_size)
        _y = y
        y += self.dims.padding * 3
        dh = self.bitmap.gfx.font.height
        for month in range(start_month, start_month + nmonths):
            month_name = datetime.strptime(str((month-1) % 12 + 1), "%m").strftime("%b")
            monthly_income = ""
            booked_monthly_income = 0
            completed_monthly_income = 0
            if month > datetime.now().month:
                booked_monthly_income = round(self._monthly_income(trips, month, ["Booked", "In-progress"]))
                monthly_income = f"(${str(booked_monthly_income)})"
            elif month == datetime.now().month:
                completed_monthly_income = round(self._monthly_income(trips, month, ["Completed"]))
                booked_monthly_income = round(self._monthly_income(trips, month, ["Booked", "In-progress"]))
                total_monthly_income = booked_monthly_income + completed_monthly_income
                monthly_income = f"${str(completed_monthly_income)} (${str(booked_monthly_income)}) => ${str(total_monthly_income)}"
            else:
                completed_monthly_income = round(self._monthly_income(trips, month, ["Completed"]))
                monthly_income = f"${str(completed_monthly_income)}"
            month_name += f": {monthly_income}"
            if top_bottom == "top":
                self.bitmap.text_box((x, y, x + w/nmonths, y + dh), month_name, halign="center", valign="center", use_baseline=False)
            else:
                self.bitmap.text_box((x, y+h, x + w/nmonths, y + h + dh), month_name, halign="center", valign="center", use_baseline=False)
            x += w / nmonths
        y += self.bitmap.gfx.font.height
        self.bitmap.gfx_pop()
        return y - _y

    def _render_month_boxes(self, x, y, w, h, trips, start_month, nmonths, top_bottom):
        self.bitmap.gfx_push()
        _y = y
        for month in range(start_month, start_month + nmonths):
            self.bitmap.rectangle((x, y, x + w/nmonths, y + h), outline="white")
            x += w / nmonths
        y += h
        self.bitmap.gfx_pop()
        return y - _y

    def _render_weekend_markers(self, x, y, w, h, trips, start_month, nmonths, top_bottom):
        self.bitmap.gfx_push()
        self.bitmap.gfx.color = "lightgray"
        cal_start = datetime(datetime.now().year, start_month, 1)
        for month in range(start_month, start_month + nmonths):
            start_day = datetime(datetime.now().year, month, 1)
            # add nmonths to start_day using relativedelta for proper month arithmetic
            end_day = start_day + relativedelta(months=nmonths)
            current_day = start_day
            while current_day < end_day:
                if current_day.weekday() >= 5: # Saturday or Sunday
                    delta_days = (current_day - cal_start).days
                    dx0 = round(w * delta_days / (nmonths * 30))
                    dx1 = round(w * (delta_days + 1) / (nmonths * 30))
                    self.bitmap.gfx.bg_color = (64,64,64)
                    self.bitmap.gfx.color = None
                    self.bitmap.rectangle((x+dx0, y, x+dx1, y+h))
                    current_day += timedelta(days=2)
                else:
                    current_day += timedelta(days=1)
        self.bitmap.gfx_pop()

    def _render_today_marker(self, y, w, h, start_month, nmonths):
        today = datetime.now()
        year_today = datetime.strptime(str(today.year), "%Y")
        dx0 = w * (today - year_today).days / (nmonths * 30)
        dw = w / (nmonths * 30) / 4
        if today.month >= start_month + 1 and today.month < start_month + nmonths + 1:
            self.bitmap.gfx_push()
            self.bitmap.gfx.color = "white"
            self.bitmap.gfx.bg_color = "red"
            self.bitmap.gfx.line_width = 2
            self.bitmap.rectangle((dx0, y, dx0+dw, y+10))
            self.bitmap.rectangle((dx0, y+h-10, dx0+dw, y+h))
            self.bitmap.gfx_pop()

    def _render_vehicle_name(self, x, y, vehicle_name, vehicle_trips):
        _y = y
        self.bitmap.gfx_push()
        self.bitmap.gfx.set_font(None, self.dims.title_font_size)
        booked_income = round(self._annual_income(vehicle_trips, ["Booked", "In-progress"]))
        completed_income = round(self._annual_income(vehicle_trips, ["Completed"]))
        days = self._annual_sum_of_days(vehicle_trips, ["Booked", "In-progress", "Completed"])
        total_income = booked_income + completed_income
        average_income = round(total_income / days, 2) if days > 0 else 0
        vehicle_name = f"{vehicle_name} - ${str(completed_income)} (${str(booked_income)}) => ${str(total_income)} ({str(days)}d * ${str(average_income)}/day)"
        self.bitmap.text(vehicle_name, x, y)
        y += self.bitmap.gfx.font.height
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
        total_completed_income = 0
        total_booked_income = 0
        total_days = 0
        for vehicle_name, vehicle_trips in self.trips.items():
            dh = self._render_vehicle_name(x, y, vehicle_name, vehicle_trips)
            y += dh
            dh = self._render_month_names(x, y, w, h, vehicle_trips, 1, nmonths, "top")
            y += dh
            h -= dh
            dh = self._render_trips(y, w, h, vehicle_name, vehicle_trips, 1, nmonths, "top")
            y += dh
            
            total_completed_income += round(self._annual_income(vehicle_trips, ["Completed"]))
            total_booked_income += round(self._annual_income(vehicle_trips, ["Booked", "In-progress"]))
            total_days += self._annual_sum_of_days(vehicle_trips, ["Booked", "In-progress", "Completed"])
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