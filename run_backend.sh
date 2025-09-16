#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
cd "$(dirname "$0")"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: python3 is not installed or not in PATH. Please install Python 3." >&2
  exit 1
fi

# Ensure dependencies are installed
if ! python3 -c "import flask" >/dev/null 2>&1; then
  echo "Installing Python dependencies (pip3 install -r requirements.txt)..."
  pip3 install -r requirements.txt
fi

export PORT="${PORT:-5001}"
echo "Starting Flask on http://localhost:${PORT}"
echo "Tip: Template pages at /old and /find_similar.html"
exec python3 app.py


