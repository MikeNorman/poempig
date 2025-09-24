#!/bin/bash
# Simple web server startup - no ML dependencies

# Always run from repo root
cd "$(dirname "$0")"

# Ensure Python virtual environment is set up and activated
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

# Install web-only dependencies
echo "Installing web dependencies..."
pip install -r requirements-web.txt

echo "Starting Flask web server with auto-reload..."
echo "🔄 Code changes will automatically restart the server"
python app.py
