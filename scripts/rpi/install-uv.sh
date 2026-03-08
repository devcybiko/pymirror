#!/bin/bash -v

set -e

# curl -LsSf https://astral.sh/uv/install.sh | sh
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
# python -m pip install --upgrade   pip
sudo apt update
# sudo apt upgrade -y
sudo xargs -a ./scripts/rpi/packages.txt apt-get install -y
sudo apt-get install -y libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev
uv sync
