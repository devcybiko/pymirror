#!/bin/bash -v

set -e

rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r ./scripts/rpi/requirements.txt
sudo apt update
sudo apt upgrade -y
sudo xargs -a ./scripts/rpi/packages.txt apt-get install -y

