#!/usr/bin/env bash
set -euo pipefail

# Always run from repo root
cd "$(dirname "$0")"

echo "🚀 Starting Flask app with minimal dependencies..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
  echo "Activating virtual environment..."
  source venv/bin/activate
else
  echo "Creating virtual environment..."
  python3 -m venv venv
  source venv/bin/activate
fi

# Install only essential dependencies
echo "Installing essential dependencies..."
pip install --upgrade pip
pip install Flask==2.3.3 flask-cors==4.0.0 python-dotenv==1.1.1

# Set environment variable to skip heavy imports
export SKIP_ML_IMPORTS=true

export PORT="${PORT:-5001}"
echo "Starting Flask on http://localhost:${PORT}"
echo "🌐 Open http://localhost:${PORT} in your browser"
exec python app.py
