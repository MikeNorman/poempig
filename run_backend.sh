#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed or not in PATH. Please install Python 3." >&2
  exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  echo "Activating virtual environment..."
  source venv/bin/activate
else
  echo "Creating virtual environment..."
  python3 -m venv venv
  source venv/bin/activate
fi

# Ensure dependencies are installed in virtual environment
if ! python -c "import flask, numpy, pandas" >/dev/null 2>&1; then
  echo "Installing Python dependencies in virtual environment..."
  echo "This may take a few minutes on first run..."
  pip install --upgrade pip
  pip install -r requirements.txt
fi

export PORT="${PORT:-5001}"
echo "Starting Flask on http://localhost:${PORT}"
echo "Tip: Template pages at /old and /find_similar.html"
exec python app.py


