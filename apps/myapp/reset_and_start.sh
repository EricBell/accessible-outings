#!/bin/bash

echo "🔄 Resetting Accessible Outings App..."

# Stop any running Flask processes
echo "📋 Stopping any running Flask processes..."
pkill -f "python.*app.py" 2>/dev/null || echo "   No Flask app was running"

# Remove database
echo "🗑️  Removing existing database..."
rm -f instance/accessible_outings.db
echo "   Database removed"

# Clean up any Python cache
echo "🧹 Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
echo "   Cache cleaned"

# Ensure requirements are installed
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt
echo "   Dependencies ready"

# Create instance directory if needed
mkdir -p instance

echo "✅ Reset complete!"
echo ""
echo "🚀 Starting the app..."
echo "   Visit: http://127.0.0.1:5000"
echo "   Press Ctrl+C to stop"
echo ""

# Start the app
python app.py