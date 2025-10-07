#!/bin/bash

source .secrets

if [ $# -eq 0 ]; then
    CONFIG="./configs/rpi/tasks.json"
else
    CONFIG="$1"
fi

    PYTHONPATH=src \
        python3 map_test.py
