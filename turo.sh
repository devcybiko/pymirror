#!/bin/bash
set -e 

rm -f ~/turo.db
sqlite3 ~/turo.db < ~/turo.sql
./run.sh ./configs/rpi02/config.json
