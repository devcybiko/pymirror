SELECT 
    *, 
    total_earnings / trip_days as earnings_per_day, 
    total_earnings / distance_traveled *100 as earnings_per_mile, 
    distance_traveled / trip_days as miles_per_day
FROM trips 
WHERE trip_status = 'Completed' 
ORDER BY trip_end
