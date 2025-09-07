#!/bin/bash

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi/config.json"
else
    CONFIG="$1"
fi

mkdir -p ./src/pmserver/static
mkdir -p ./caches/

while true; do
    PYTHONPATH=src \
        python3 -u -m pymirror.pymirror\
        --config "$CONFIG" \
        --output_file=null \
        --frame_buffer="/dev/fb0" \
        >> src/pmserver/static/output.log 2>&1
        date
        echo "Restarting pymirror..."
done