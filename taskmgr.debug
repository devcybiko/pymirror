#!/bin/bash

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi/tasks.json"
else
    CONFIG="$1"
fi

while true; do
    PYTHONPATH=src \
        python3 -u -m pmtaskmgr.pmtaskmgr \
        --config "$CONFIG"
        date
        echo "Restarting pmtaskmgr..."
        sleep 10
done                                                                                    