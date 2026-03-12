from datetime import datetime
import sys
sys.path.append("./libs")

from glslib.to_types import to_munch
from glslib.glsdb import GLSDb
from glslib.strings import expand_string
from munch import DefaultMunch
from glslib.gson import json_print

DEPRECIATION_PER_MILE = 0.085
MAX_MILES = 150_000

class MyMunch(DefaultMunch):
    def __init__(self, type=None, **kwargs):
        super().__init__(**kwargs)
        # Store _type as a true instance attribute, not a dict key
        object.__setattr__(self, '_type', type or MyMunch)

    @classmethod
    def fromDict(cls, dct):
        munch = MyMunch()
        for key, value in dct.items():
            if isinstance(value, dict):
                munch[key] = cls.fromDict(value)
            elif isinstance(value, list):
                munch[key] = [cls.fromDict(item) if isinstance(item, dict) else item for item in value]
            else:
                munch[key] = value
        return munch

    def __getitem__(self, key):
        try:
            value = super().__getitem__(key)
        except KeyError:
            # If the key doesn't exist, create an empty instance
            type_class = object.__getattribute__(self, '_type')
            if type_class == MyMunch:
                value = DefaultMunch()
                value.__class__ = MyMunch
            else:
                value = type_class()
            dict.__setitem__(self, key, value)
            return value
        
        # If the value is None, create an empty type and store it
        if value is None:
            type_class = object.__getattribute__(self, '_type')
            if type_class == MyMunch:
                empty_value = DefaultMunch()
                empty_value.__class__ = MyMunch
            else:
                empty_value = type_class()
            dict.__setitem__(self, key, empty_value)
            return empty_value
        return value

def main():
    ## gather data
    db_path = expand_string("$HOME/turo.db", {})
    db = GLSDb(f"sqlite:///{db_path}")
    trips = db.query("SELECT * FROM trips where trip_status = 'Completed'")
    vehicles = db.query("SELECT * FROM vehicles")

    ## coallate trips
    trip_data = MyMunch()
    x_axis = set()
    for _vehicle in vehicles:
        vehicle = MyMunch.fromDict(_vehicle)
        for _trip in trips:
            trip = MyMunch.fromDict(_trip)
            if trip.distance_traveled:
                trip_start = trip.trip_start.strftime("%Y-%m-%d")
                x_axis.add(trip_start)
                trip_data[vehicle.nickname][trip_start] = trip
    json_print(trip_data)
    x_axis = sorted(list(x_axis))
    json_print(x_axis)

    ## coallate cars
    cars = MyMunch()
    for _vehicle in vehicles:
        vehicle = MyMunch.fromDict(_vehicle)
        cars[vehicle.nickname] = vehicle
    
    ## calculate depreciation
    for vehicle_nickname, trips in trip_data.items():
        last_trip = None
        for trip_date in x_axis:
            trip = trips[trip_date]
            if trip.vehicle_nickname != vehicle_nickname:
                continue
            if last_trip is None:
                trip.vehicle_value = cars[vehicle_nickname].last_kbb_value
                trip.vehicle_miles = trip.check_in_odometer
                trip.miles_remaining = MAX_MILES - trip.vehicle_miles
                trip.cumulative_earnings = 0
                last_trip = trip
            trip.vehicle_miles = trip.check_out_odometer
            delta_miles = trip.vehicle_miles - last_trip.vehicle_miles
            trip.vehicle_value = last_trip.vehicle_value - (delta_miles * DEPRECIATION_PER_MILE)
            trip.miles_remaining = MAX_MILES - trip.vehicle_miles
            trip.cumulative_earnings = last_trip.cumulative_earnings + trip.total_earnings
            last_trip = trip
    
    ## print depreciation
    totol_equity = 0
    total_income = 0
    total_depreiation = 0
    for vehicle_nickname, trips in trip_data.items():
        print(f"Vehicle: {vehicle_nickname}")
        first_trip = None
        last_trip = None
        for trip_date in x_axis:
            trip = trips[trip_date]
            if trip.vehicle_nickname != vehicle_nickname:
                continue
            if first_trip is None:
                first_trip = trip
            last_trip = trip
            print(f"  Trip on {trip.trip_start}-{trip.trip_end}: Value: ${trip.vehicle_value:.0f}, Miles: {trip.vehicle_miles}")
        print("total depreciation:")
        print(first_trip.trip_start, last_trip.trip_start)
        delta_miles = last_trip.vehicle_miles - first_trip.vehicle_miles
        delta_days = (last_trip.trip_end - first_trip.trip_start).days + 1
        print("... ${:.0f} initial value".format(cars[vehicle_nickname].last_kbb_value))
        print("... ${:.0f} amount owed".format(cars[vehicle_nickname].remaining_balance))
        print("... ${:.0f} final value".format(last_trip.vehicle_value))
        print("... ${:.0f} depreciation".format(first_trip.vehicle_value - last_trip.vehicle_value))
        print("... ${:.0f} equity".format(last_trip.vehicle_value - cars[vehicle_nickname].remaining_balance))
        print("... {:.0f} last odo".format(last_trip.vehicle_miles))
        print("... {:.0f} miles driven".format(delta_miles))
        print("... {:.0f} days driven".format(delta_days))
        print("... {:.0f} miles per day".format(delta_miles / delta_days if delta_days else 0))
        print("... ${:.3f} depreciation per mile".format((first_trip.vehicle_value - last_trip.vehicle_value) / delta_miles))
        print("... ${:.0f} cumulative earnings".format(last_trip.cumulative_earnings))
        print("... ${:.3f} $/mile".format(last_trip.cumulative_earnings / delta_miles if delta_miles else 0))
        print("... {:.0f} miles remaining".format(last_trip.miles_remaining))
        totol_equity += last_trip.vehicle_value - cars[vehicle_nickname].remaining_balance
        total_income += last_trip.cumulative_earnings
        total_depreiation += first_trip.vehicle_value - last_trip.vehicle_value
    print("Total equity: ${:.0f}".format(totol_equity))
    print("Total income: ${:.0f}".format(total_income))
    print("Total depreciation: ${:.0f}".format(total_depreiation))
    print("Total equity + income: ${:.0f}".format(totol_equity + total_income))

main()