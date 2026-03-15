#!/bin/bash

python ./turo_depreciation.py

sqlite3 ~/turo.db << EOF
DROP TABLE IF EXISTS depreciation;

CREATE TABLE depreciation (
  vehicle TEXT,
  trip_date DATE,
  trip_start DATETIME,
  trip_end DATETIME,
  value REAL,
  miles INTEGER,
  delta_miles INTEGER,
  delta_days INTEGER,
  cumulative_earnings REAL,
  miles_remaining INTEGER,
  initial_value REAL,
  amount_owed REAL,
  final_value REAL,
  depreciation REAL,
  equity REAL,
  last_odo INTEGER,
  miles_driven INTEGER,
  days_driven INTEGER,
  miles_per_day REAL,
  depreciation_per_mile REAL,
  cumulative_earnings_per_mile REAL,
  earnings_per_mile REAL
);

.mode csv
.import --skip 1 "turo_depreciation.csv" depreciation
EOF


