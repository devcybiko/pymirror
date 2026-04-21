
from datetime import datetime, timedelta

from munch import DefaultMunch

from pymirror.pmtile import TileConfig
from glslib.glsdb import GLSDb
from glslib.to_types import to_munch
from glslib.strftime import strftime_by_example
from pymirror.pmcard import PMCard
from tables.turo_trips_table import TuroTripsTable

class TuroNextTile(PMCard):
    def __init__(self, pm, config: TileConfig):
        super().__init__(pm, config)
        self._turo: DefaultMunch = to_munch(config.turo_next)
        self.turo_db = GLSDb(self._turo.database_url)
        self.date_format = strftime_by_example(self._turo.date_format or "%Y-%m-%d")
        self.time_format = strftime_by_example(self._turo.time_format or "%H:%M:%S")

    def _format_msg(self, trip, trip_date: datetime, call_to_action: str):
        nbs = "\u00A0"  # non-breaking space
        tab = nbs * 4
        now = datetime.now()
        today = now.date()
        tomorrow = (now + timedelta(days=1)).date()
        trip_date_only = trip_date.date()
        
        if trip_date_only == today:
            returning_in = "TODAY"
        elif trip_date_only == tomorrow:
            returning_in = "TOMORROW"
        else:
            days = (trip_date_only - today).days
            returning_in = f"in {days} days"
        msg = ""
        msg += f"{call_to_action} ({returning_in})\n"
        msg += f"{tab}{trip_date.strftime(self.date_format)}\n"
        msg += f"{tab}{trip_date.strftime(self.time_format)} ({trip.trip_days} days)\n"
        msg += f"{tab}{trip.guest}: (${trip.total_earnings})\n"
        return msg
    
    def exec(self) -> bool:
        if not self.timer.is_timedout(): 
            return False
            # return is_dirty # early exit if not timed out
        self.timer.reset(self._turo.refresh_time)
        trips = self.turo_db.get_all_where(TuroTripsTable, f"vehicle_nickname='{self._turo.vehicle_nickname}'", order_by="trip_start")
        self.set_header(f"Turo - {self._turo.vehicle_nickname}")
        msg = ""
        for trip in trips:
            if trip.trip_status == "Booked":
                msg += self._format_msg(trip, trip.trip_start, "PICK UP")
                msg += " \n"
                msg += self._format_msg(trip, trip.trip_end, "DROP OFF")
                msg += " \n"
            elif trip.trip_status == "In-progress":
                msg += self._format_msg(trip, trip.trip_end, "DROP OFF")
                msg += " \n"
            else:
                pass # canceled or other
        now = datetime.now()
        self.set_footer(f"Last updated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.set_body(msg)
        return True # state changed