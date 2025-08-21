#!/bin/bash

# Sale Tracker Installation Script
# This script installs the Sale Tracker application and its dependencies

set -e  # Exit on any error

echo "🚀 Sale Tracker Installation Script"
echo "=================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python $PYTHON_VERSION found"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install --break-system-packages -r requirements.txt

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating template..."
    cat > .env << EOF
SENDER_EMAIL=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
RECIPIENT_EMAIL=recipient@example.com
RECIPIENT_EMAIL2=recipient2@example.com
EOF
    echo "📝 Please edit .env file with your email credentials"
else
    echo "✅ .env file found"
fi

# Make CLI executable
chmod +x cli.py

# Test installation
echo "🧪 Testing installation..."
python3 test_sale_tracker.py

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your email credentials"
echo "2. Test the application: python3 cli.py test-scraping"
echo "3. Send a test email: python3 cli.py send-test"
echo "4. Start the scheduler: python3 cli.py run"
echo ""
echo "For more information, see README_IMPROVED.md"
