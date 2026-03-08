#!/bin/bash -v

set -e

brew install sdl2 sdl2_mixer

rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r ./scripts/macos/requirements.txt
