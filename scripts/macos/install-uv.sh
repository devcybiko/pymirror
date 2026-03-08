#!/bin/bash -v

set -e

brew install sdl2 sdl2_mixer

rm -rf .venv
cp ./scripts/macos/pyproject.toml .
uv sync