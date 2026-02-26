#!/bin/bash
# Set up the project: create venv and install dependencies
set -e
cd "$(dirname "$0")/.."

echo "Creating virtual environment..."
uv venv

echo "Installing dependencies..."
uv pip install -r requirements.txt

echo ""
echo "Done. Activate with: source .venv/bin/activate"
echo "Make sure your .env has OPENROUTER_API_KEY set."
