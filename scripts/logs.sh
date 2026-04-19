#!/bin/bash

set -e

tail $@ -f ./apps/pymirror/pmserver/static/output.log
