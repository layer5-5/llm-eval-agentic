#!/bin/bash
# Run eval against a single model
# Usage: .tools/run-eval.sh <model>
# Example: .tools/run-eval.sh openrouter/meta-llama/llama-3.3-70b-instruct
set -e
cd "$(dirname "$0")/.."

if [ -z "$1" ]; then
    echo "Usage: .tools/run-eval.sh <model>"
    echo "Example: .tools/run-eval.sh openrouter/meta-llama/llama-3.3-70b-instruct"
    exit 1
fi

.venv/bin/python eval/harness.py --model "$1"
