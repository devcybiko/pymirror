#!/bin/bash

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi/config.json"
else
    CONFIG="$1"
fi

mkdir -p ./src/pmserver/static
mkdir -p ./caches/
source .venv/bin/activate

while true; do
    PYTHONPATH="libs:apps/pymirror" \
        python3 -u -m pymirror.pymirror\
        --config "$CONFIG" \
        --output_file=null \
        --frame_buffer="/dev/fb0" \
        >> ./apps/pymirror/pmserver/static/output.log 2>&1
        date
        echo "Restarting pymirror..."
        sleep 10
done
