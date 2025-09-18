#!/bin/bash -v

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi/tasks.json"
else
    CONFIG="$1"
fi

while true; do
    PYTHONPATH=src \
        python3 -u -m pmtaskmgr.pmtaskmgr \
        --config "$CONFIG" \
        --output_file=null \
        --frame_buffer="/dev/fb0" \
        >> src/pmserver/static/tasks.log 2>&1
        date
        echo "Restarting pmtaskmgr..."
done                                                                                    