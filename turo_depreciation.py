import csv
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
    total_equity = 0
    total_income = 0
    total_depreciation = 0
    ## open a file for .csv otuput using the standard library csv module
    
    header_written = False
    with open('turo_depreciation.csv', 'w', newline='') as csvfile:
        # lowercase the fieldnames and replace spaces with underscores
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
                record = MyMunch()
                record.vehicle = vehicle_nickname
                record.trip_date = trip_date
                record.trip_start = trip.trip_start
                record.trip_end = trip.trip_end
                record.value = trip.vehicle_value
                record.miles = trip.vehicle_miles
                record.delta_miles = trip.vehicle_miles - first_trip.vehicle_miles
                record.delta_days = (trip.trip_end - first_trip.trip_start).days + 1
                record.cumulative_earnings = trip.cumulative_earnings
                record.miles_remaining = trip.miles_remaining
                record.initial_value = cars[vehicle_nickname].last_kbb_value
                record.amount_owed = cars[vehicle_nickname].remaining_balance
                record.final_value = last_trip.vehicle_value
                record.depreciation = first_trip.vehicle_value - last_trip.vehicle_value
                record.equity = last_trip.vehicle_value - cars[vehicle_nickname].remaining_balance
                record.last_odo = last_trip.vehicle_miles
                record.miles_driven = last_trip.vehicle_miles - first_trip.vehicle_miles
                record.days_driven = (last_trip.trip_end - first_trip.trip_start).days + 1
                record.miles_per_day = record.miles_driven / record.days_driven if record.days_driven else 0
                record.depreciation_per_mile = record.depreciation / record.miles_driven if record.miles_driven else 0
                record.cumulative_earnings_per_mile = record.cumulative_earnings / record.miles_driven if record.miles_driven else 0
                record.earnings_per_mile = record.cumulative_earnings / record.miles_driven if record.miles_driven else 0
                record.miles_remaining = last_trip.miles_remaining

                if header_written == False:
                    fieldnames = record.keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    header_written = True

                writer.writerow(record)
                print(f"  Trip on {trip.trip_start}-{trip.trip_end}: Value: ${trip.vehicle_value:.0f}, Miles: {trip.vehicle_miles}")
                print("total depreciation:")
                print(record.trip_start, record.trip_start)
                print("... ${:.0f} initial value".format(record.initial_value))
                print("... ${:.0f} amount owed".format(record.amount_owed))
                print("... ${:.0f} final value".format(record.final_value))
                print("... ${:.0f} depreciation".format(record.depreciation))
                print("... ${:.0f} equity".format(record.equity))
                print("... {:.0f} last odo".format(record.last_odo))
                print("... {:.0f} miles driven".format(record.miles_driven))
                print("... {:.0f} days driven".format(record.days_driven))
                print("... {:.0f} miles per day".format(record.miles_per_day))
                print("... ${:.3f} depreciation per mile".format(record.depreciation_per_mile))
                print("... ${:.0f} cumulative earnings".format(record.cumulative_earnings))
                print("... ${:.3f} $/mile".format(record.cumulative_earnings_per_mile))
                print("... {:.0f} miles remaining".format(record.miles_remaining))
                total_equity += record.equity
                total_income += record.cumulative_earnings
                total_depreciation += record.depreciation
        print("Total equity: ${:.0f}".format(total_equity))
        print("Total income: ${:.0f}".format(total_income))
        print("Total depreciation: ${:.0f}".format(total_depreciation))
        print("Total equity + income: ${:.0f}".format(total_equity + total_income))

main()