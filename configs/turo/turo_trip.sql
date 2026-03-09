    SELECT 
        vehicle_nickname as vehicle, 
        guest, 
        trip_status as status, 
        strftime('%Y-%m-%d', trip_start) AS start, 
        -- strftime('%Y-%m-%d', trip_end) AS trip_end, 
        -- check_in_odometer,
        -- check_out_odometer,
        trip_days as 'days', 
CASE 
  WHEN check_in_odometer = '' OR check_out_odometer ='' THEN '' 
  ELSE check_out_odometer - check_in_odometer 
END AS distance, 
CASE 
  WHEN check_in_odometer = '' OR check_out_odometer = '' OR ROUND(trip_days) = '' OR ROUND(trip_days) = 0 THEN '' 
  ELSE CAST(ROUND((check_out_odometer - check_in_odometer) / ROUND(trip_days)) AS INTEGER) 
END AS 'mi/day', 
CASE 
  WHEN check_in_odometer = '' OR check_out_odometer = '' OR ROUND(trip_days) = '' OR ROUND(trip_days) = 0 THEN '' 
  ELSE '$' || ROUND(total_earnings / ROUND(trip_days), 2) 
END AS '$$/day', 
CASE 
  WHEN check_in_odometer = '' OR check_out_odometer = '' OR check_out_odometer - check_in_odometer = 0 THEN '' 
  ELSE '$' || ROUND(total_earnings / (check_out_odometer - check_in_odometer), 2) 
END AS "$$/mi", 
    '$' || CAST(ROUND(SUM(total_earnings) OVER (ORDER BY trip_start),0) AS INTEGER) AS "Total $$" 
        FROM trips 
WHERE trip_status in ('Completed', 'In-progress', 'Booked') 
AND vehicle_nickname = '{vehicle_nickname}' 
AND trip_start >= date('now', '-{months_ago} month') 
ORDER BY trip_start 
