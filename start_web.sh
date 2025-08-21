#!/bin/bash

# Sale Tracker Web Application Startup Script

echo "🌐 Starting Sale Tracker Web Application..."
echo "=========================================="

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip3 install --break-system-packages flask
fi

# Start the web application
echo "🚀 Starting web server on http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo ""

# Kill any existing Flask processes
pkill -f "python3 web_app.py" 2>/dev/null || true

# Start the web application
python3 web_app.py
