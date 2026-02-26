#!/bin/bash
# Generate aggregate report from all eval runs
set -e
cd "$(dirname "$0")/.."

.venv/bin/python eval/report.py
