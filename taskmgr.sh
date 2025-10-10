#!/bin/bash

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi/tasks.json"
else
    CONFIG="$1"
fi
source .venv/bin/activate
while true; do
    PYTHONPATH=src \
        python3 -u -m pmtaskmgr.pmtaskmgr \
        --config "$CONFIG" \
        >> src/pmserver/static/output.log 2>&1
        date
        echo "Restarting pmtaskmgr..."
        sleep 10
done                                                                                    