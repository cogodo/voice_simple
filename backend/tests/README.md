# Tests Directory

This directory contains all test files and debugging tools for the Voice Agent backend.

## Test Files

### 🎤 **TTS (Text-to-Speech) Tests**

- **`test_streaming.py`** - Direct test of the TTS streaming function
  - Tests `my_processing_function_streaming()` directly
  - Validates audio chunk generation and base64 decoding
  - Run: `python test_streaming.py`

- **`test_socketio_tts.py`** - Socket.IO TTS streaming test
  - Tests TTS via Socket.IO events (full integration)
  - Uses Python Socket.IO client
  - Run: `python test_socketio_tts.py`

- **`test_cartesia_direct.py`** - Direct Cartesia API test
  - Low-level test of Cartesia SSE API
  - Inspects raw response structure
  - Run: `python test_cartesia_direct.py`

### 🌐 **WebSocket & Integration Tests**

- **`test_websocket.py`** - WebSocket connection test
  - Basic WebSocket connectivity test
  - Run: `python test_websocket.py`

- **`test_complete_flow.py`** - End-to-end flow test
  - Complete conversation flow testing
  - Run: `python test_complete_flow.py`

### 🐛 **Debug Tools**

- **`debug_audio_timing.py`** - Audio timing analysis
  - Analyzes audio chunk timing and gaps
  - Identifies streaming performance issues
  - Run: `python debug_audio_timing.py`

- **`debug_auto_tts.py`** - Auto-TTS debugging
  - Debugging tool for automatic TTS features
  - Run: `python debug_auto_tts.py`

### 🔍 **Browser-Based Tests**

- **`static/test_tts.html`** - Interactive TTS test page
  - Browser-based Socket.IO TTS testing
  - Real-time event logging
  - Access: `http://localhost:8000/test`

## Running Tests

### Prerequisites
Make sure the backend server is running:
```bash
cd backend
python app.py
```

### Quick Test Commands
```bash
# Test TTS streaming function directly
python tests/test_streaming.py

# Test via Socket.IO (requires server running)
python tests/test_socketio_tts.py

# Test Cartesia API directly
python tests/test_cartesia_direct.py

# Browser-based test (server must be running)
# Open: http://localhost:8000/test
```

### Debug Commands
```bash
# Analyze audio timing issues
python tests/debug_audio_timing.py

# Debug auto-TTS features
python tests/debug_auto_tts.py
```

## Test Environment

All tests should be run from the `backend/` directory with the virtual environment activated:

```bash
cd backend
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
python tests/[test_file].py
```

## Expected Results

- **TTS Streaming**: Should receive 100+ audio chunks (~140 typical)
- **Socket.IO**: Should connect and receive audio events
- **Cartesia API**: Should return base64-encoded audio data
- **Audio Timing**: Should show consistent ~23ms intervals between chunks

## Troubleshooting

- **Connection Issues**: Check if backend server is running on port 8000
- **API Issues**: Verify `CARTESIA_API_KEY` and `OPENAI_API_KEY` are set
- **Audio Issues**: Check `debug_audio_timing.py` for timing problems
- **Browser Issues**: Use Chrome/Firefox, check console for WebSocket errors 