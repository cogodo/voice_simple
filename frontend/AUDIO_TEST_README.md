# Cartesia Audio Streaming Test

This test file comprehensively analyzes the audio streaming performance from Cartesia through WebSocket, logging detailed packet timing data.

## 🎯 What It Tests

- **WebSocket Connection**: Connection time and stability
- **Frame Delivery**: PCM frame reception timing and intervals  
- **Performance Metrics**: FPS, bytes/second, frame sizes
- **Timing Analysis**: Frame intervals, fast/slow frames, delivery rate
- **Complete Logging**: Every packet timestamped with full metadata

## 🚀 How to Run

### Option 1: Simple Script
```bash
./run_audio_test.sh
```

### Option 2: Manual
```bash
# 1. Make sure backend is running
cd ../backend && python main.py

# 2. Run the test
cd ../frontend
dart test_audio_streaming.dart
```

## 📊 Output

The test generates two types of output:

### 1. Console Output (Real-time)
- Connection status
- Frame-by-frame logging every 25 frames
- Real-time performance metrics
- Summary report at the end

### 2. JSON Report (`audio_streaming_test_results.json`)
Complete detailed analysis including:

```json
{
  "test_metadata": {
    "test_start_time": "2024-01-XX...",
    "total_test_duration_ms": 12450,
    "test_text": "Hello! This is a comprehensive test...",
    "websocket_url": "http://localhost:8000"
  },
  "timing_summary": {
    "frames_received": 538,
    "streaming_duration_ms": 11200,
    "time_to_first_frame_ms": 850,
    "frame_delivery_rate_percent": 99.6
  },
  "frame_rate_analysis": {
    "average_fps": 47.2,
    "average_interval_ms": 21.2,
    "fast_frames_percent": 15.2,
    "slow_frames_percent": 8.1
  },
  "detailed_logs": {
    "events": [...],      // All events with timestamps
    "frames": [...],      // Every frame with timing data
    "frame_intervals": [...]  // All intervals for analysis
  }
}
```

## 🔍 Key Metrics Analyzed

### Performance Metrics
- **Average FPS**: Target is 50fps (20ms frames)
- **Frame Delivery Rate**: Percentage of expected frames received
- **Bytes/Second**: Data transfer rate
- **Time to First Frame**: Latency from request to first audio

### Timing Analysis  
- **Fast Frames**: <15ms intervals (too fast)
- **Normal Frames**: 15-25ms intervals (good)
- **Slow Frames**: >25ms intervals (too slow)
- **Min/Max Intervals**: Range of frame timing

### Frame Logging
Every PCM frame includes:
- Absolute timestamp
- Relative time from test start  
- Frame size in bytes
- Interval from previous frame
- Running totals and averages

## 🎛️ Configuration

Edit the test file to modify:

```dart
// Test configuration
static const String WEBSOCKET_URL = 'http://localhost:8000';
static const String TEST_TEXT = 'Your test text here...';
static const String OUTPUT_FILE = 'audio_streaming_test_results.json';
```

## 📈 Interpreting Results

### Good Performance
- **Average FPS**: 45-50 fps
- **Fast Frames**: <10%
- **Slow Frames**: <15%  
- **Delivery Rate**: >95%
- **Time to First Frame**: <1000ms

### Problem Indicators
- **High Fast Frames**: Backend sending too quickly
- **High Slow Frames**: Network delays or processing issues
- **Low Delivery Rate**: Frames being dropped
- **High First Frame Time**: Connection or processing latency

## 🛠️ Troubleshooting

### Backend Not Running
```
❌ Backend not running! Please start the backend first:
   cd ../backend && python main.py
```

### WebSocket Connection Issues
- Check if backend is accessible at `localhost:8000`
- Verify WebSocket endpoint is working
- Check firewall/network settings

### No Frames Received
- Verify TTS request format matches backend API
- Check backend logs for TTS processing errors
- Ensure Cartesia API is working in backend

This test provides comprehensive analysis to optimize your audio streaming performance! 🎵 