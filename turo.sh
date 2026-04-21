#!/bin/bash
set -e 

rm -f ~/trips.db
sqlite3 ~/trips.db < ~/trips.sql
./run.sh ./configs/rpi02/config.json
