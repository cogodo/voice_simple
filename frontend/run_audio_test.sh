#!/bin/bash

echo "🧪 Cartesia Audio Streaming Test Runner"
echo "========================================"

# Check if backend is running
echo "🔍 Checking if backend is running..."
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Backend not running! Please start the backend first:"
    echo "   cd ../backend && python main.py"
    exit 1
fi
echo "✅ Backend is running"

# Check dependencies
echo "🔍 Checking Flutter dependencies..."
if ! flutter doctor > /dev/null 2>&1; then
    echo "❌ Flutter not found! Please install Flutter first."
    exit 1
fi

echo "📦 Getting dependencies..."
flutter pub get

echo "🚀 Running audio streaming test..."
echo "📝 Test will create: audio_streaming_test_results.json"
echo ""

# Create a temporary Flutter app structure to run the test
echo "🔧 Setting up Flutter test environment..."

# Create a temporary main.dart that runs our test
cat > lib/main_test.dart << 'EOF'
import 'package:flutter/material.dart';
import '../test_audio_streaming.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  print('🚀 Starting Flutter-based audio streaming test...');
  
  // Run the test
  final test = AudioStreamingTest();
  await test.runTest();
  
  print('✅ Test execution completed - check audio_streaming_test_results.json');
  
  // Exit the app
  exit(0);
}
EOF

# Run the test through Flutter
echo "🎵 Executing test with live audio playback..."
flutter run -d chrome --target=lib/main_test.dart

# Cleanup
rm -f lib/main_test.dart

echo ""
echo "✅ Test completed!"
if [ -f "audio_streaming_test_results.json" ]; then
    echo "📄 Results saved to: audio_streaming_test_results.json"
    echo "📊 You can view the detailed JSON report for analysis"
else
    echo "⚠️ No results file found - check for errors above"
fi 