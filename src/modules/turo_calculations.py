def all_time_income(trips, status_list=["Booked", "Completed", "In-progress"]):
    total = 0
    for trip in trips:
        if trip.trip_status in status_list:
            total += trip.total_earnings
    return total

def annual_income(trips, status_list=["Booked", "Completed", "In-progress"]):
    total = 0
    for trip in trips:
        if trip.trip_status in status_list:
            total += trip.total_earnings
    return total

def monthly_income(trips, start_date, status_list=["Booked", "Completed", "In-progress"]):
    total = 0
    for trip in trips:
        if trip.trip_status not in status_list:
            continue
        if trip.trip_end.month == start_date.month:
            total += trip.total_earnings
    return round(total, 2)

def annual_sum_of_days(trips, status_list=["Booked", "Completed", "In-progress"]):
    total = 0
    for trip in trips:
        if trip.trip_status not in status_list:
            continue
        total += trip.trip_days
    return total
    
