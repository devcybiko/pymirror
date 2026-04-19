#!/bin/bash

set -e

tail -n 100 -f ./apps/pymirror/pmserver/static/output.log
