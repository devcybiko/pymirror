#!/bin/bash

set -e

OPTS="$@"
tail -f ./apps/pymirror/pmserver/static/output.log "$OPTS" 
