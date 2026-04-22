#!/bin/bash
set -e 

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi02/config.json"
else
    CONFIG="$1"
fi


rm -f ~/turo.db
sqlite3 ~/turo.db < ~/turo.sql
./run.sh "$CONFIG"
