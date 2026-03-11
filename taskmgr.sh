#!/bin/bash

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi01/tasks.json"
else
    CONFIG="$1"
fi

rm ./maps/*
mkdir -p ./maps

source .venv/bin/activate
while true; do
    PYTHONPATH=libs:apps/pmtaskmgr \
        python3 -u -m pmtaskmgr \
        --config "$CONFIG" \
        >> apps/pymirror/pmserver/static/ 2>&1
        date
        echo "Restarting pmtaskmgr..."
        sleep 10
done                                                                                    