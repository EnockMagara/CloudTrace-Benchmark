#!/bin/bash

# CloudTrace Setup Script for Local Development
# This script sets up a local development environment for CloudTrace

# Exit on error
set -e

echo "=== CloudTrace Development Environment Setup ==="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.7.0"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required, you have $python_version"
    exit 1
fi

echo "✓ Python version $python_version detected"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create data directory if it doesn't exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
    echo "✓ Data directory created"
else
    echo "✓ Data directory already exists"
fi

# Set permissions (only on Unix-like systems)
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    echo "Setting permissions..."
    # Make setup.sh executable
    chmod +x setup.sh
    # Make data directory writable
    chmod -R 755 data
    echo "✓ Permissions set"
fi

echo "=== Setup Complete ==="
echo ""
echo "To start the application in development mode:"
echo "1. Activate the virtual environment (if not already activated):"
echo "   source venv/bin/activate"
echo ""
echo "2. Run the application (with appropriate permissions for traceroute):"
echo "   sudo python app.py"
echo ""
echo "Note: CloudTrace requires elevated privileges for traceroute functionality."
echo "      Run the application with sudo (Linux/macOS) or as Administrator (Windows)."
echo ""
echo "Happy developing!" 