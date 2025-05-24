#!/bin/bash

# Voice Agent Backend Runner Script
# This script sets up the environment and runs the backend server

set -e  # Exit on any error

echo "======================================"
echo "Voice Agent Backend Server"
echo "======================================"

# Navigate to backend directory
cd "$(dirname "$0")/../backend"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  WARNING: No .env file found!"
    echo "Please create a .env file with your API keys:"
    echo "OPENAI_API_KEY=your_openai_key_here"
    echo "CARTESIA_API_KEY=your_cartesia_key_here"
    echo ""
    echo "You can copy .env.example and fill in your keys."
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Create temp_audio directory if it doesn't exist
mkdir -p temp_audio

# Run the application
echo "Starting Voice Agent Backend..."
echo "Server will run on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo "======================================"

python app.py 