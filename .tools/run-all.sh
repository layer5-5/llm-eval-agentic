#!/bin/bash
# Run eval (bash + mcp) against all models in models.yaml
set -e
cd "$(dirname "$0")/.."

.venv/bin/python eval/harness.py --all

echo ""
echo "Generating aggregate report..."
.venv/bin/python eval/report.py
