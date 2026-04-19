#!/bin/bash

set -e

OPTS="$@"
tail "$OPTS" -f apps/pymirror/pmserver/static/output.log
