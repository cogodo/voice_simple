#!/bin/bash

# Voice Agent Frontend Runner Script
# This script sets up the Flutter environment and runs the frontend app

set -e  # Exit on any error

echo "======================================"
echo "Voice Agent Flutter Frontend"
echo "======================================"

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend"

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter is not installed!"
    echo "Please install Flutter from https://docs.flutter.dev/get-started/install"
    exit 1
fi

# Run Flutter doctor to check setup
echo "Checking Flutter installation..."
flutter doctor --android-licenses > /dev/null 2>&1 || true

# Get dependencies
echo "Getting Flutter dependencies..."
flutter pub get

# Check for connected devices
echo "Checking for connected devices..."
DEVICES=$(flutter devices --machine | jq -r '.[].id' 2>/dev/null || echo "")

if [ -z "$DEVICES" ]; then
    echo "⚠️  No devices found. Please:"
    echo "   • Connect an Android device via USB with USB debugging enabled"
    echo "   • Start an Android emulator"
    echo "   • Start an iOS simulator (macOS only)"
    echo ""
    echo "Available options:"
    flutter devices
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Ask which device to use if multiple available
echo "Available devices:"
flutter devices

echo ""
echo "Starting Flutter app..."
echo "======================================"

# Run the app
flutter run 