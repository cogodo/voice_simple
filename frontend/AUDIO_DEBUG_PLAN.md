# Audio Debugging Plan: Distorted & Truncated Audio Issue

## Problem Summary
- **Symptoms**: Audio comes through but only first few chunks, extremely distorted
- **Evidence**: Backend logs show 654 chunks sent successfully over 19.54s
- **Scope**: Issue likely in frontend audio processing/playback chain

## Phase 1: Initial Investigation

### 1.1 Examine Frontend Audio Chain
Search for and analyze these key components:
```bash
# Search patterns for LLM to use:
- "AudioPlayer" OR "audio_player" OR "just_audio"
- "SocketIO" AND "tts_audio" 
- "chunk" AND "audio"
- "Uint8List" OR "bytes" AND "audio"
- "StreamController" OR "Stream" AND "audio"
```

**Key Files to Examine**:
- Audio player implementation
- SocketIO event handlers for TTS
- Audio streaming/buffering logic
- Audio format conversion code

### 1.2 Check Audio Format Compatibility
**Backend Output**: `pcm_f32le` → `int16` (22050 Hz, mono)
**Frontend Expected**: Verify what format Flutter audio player expects

**Investigation Steps**:
1. Find audio player initialization code
2. Check supported formats and sample rates
3. Verify endianness handling (little-endian)
4. Confirm bit depth expectations (16-bit vs 32-bit)

## Phase 2: SocketIO Communication Analysis

### 2.1 WebSocket Event Handling
Search for:
```dart
// Event listener patterns
socket.on('tts_audio_chunk', ...)
socket.on('tts_finished', ...)
```

**Verify**:
- Event names match backend (`tts_audio_chunk`)
- Chunk data extraction from JSON
- Base64 decoding if used
- Error handling in event callbacks

### 2.2 Data Flow Validation
**Backend sends**:
```json
{
  "audio_data": [255,254,253,...], // Raw bytes array
  "chunk_type": "tts_audio",
  "chunk_number": 654,
  "timestamp": 19.508662223815918
}
```

**Frontend should**:
1. Extract `audio_data` array
2. Convert to `Uint8List`
3. Buffer or stream to audio player
4. Handle chunk ordering

## Phase 3: Audio Player Integration

### 3.1 Streaming vs Buffering Strategy
**Current Backend**: Sends 1024-byte chunks at 23ms intervals

**Frontend Options**:
- **Stream directly**: Feed chunks to real-time audio stream
- **Buffer then play**: Collect chunks, create complete audio file
- **Hybrid**: Buffer initial chunks, then stream

### 3.2 Audio Player Configuration Issues
Common problems to check:
```dart
// Sample rate mismatch
AudioPlayer(sampleRate: 44100) // Should be 22050

// Format mismatch  
AudioFormat.pcm16bit // Correct for int16
AudioFormat.pcm32float // Wrong - backend converts to int16

// Endianness issues
ByteData.view(bytes.buffer, 0, bytes.length)
```

## Phase 4: Specific Bug Patterns to Search

### 4.1 Chunk Accumulation Problems
Look for:
```dart
// Problematic patterns
List<int> audioBuffer = [];
audioBuffer.addAll(chunkData); // Memory issues?

// Buffer overflow
if (audioBuffer.length > maxSize) {
  audioBuffer.clear(); // Losing data?
}
```

### 4.2 Timing and Synchronization Issues
```dart
// Race conditions
Timer? audioTimer;
audioTimer?.cancel(); // Premature stopping?

// Async issues
await audioPlayer.play(); // Blocking subsequent chunks?
```

### 4.3 Data Corruption Patterns
```dart
// Type conversion errors
List<dynamic> rawData = json['audio_data'];
Uint8List bytes = Uint8List.fromList(rawData.cast<int>());
// Check: Are values > 255? Negative values?

// Endianness problems
ByteData byteData = ByteData.view(uint8List.buffer);
int16Value = byteData.getInt16(offset, Endian.little); // Correct
int16Value = byteData.getInt16(offset, Endian.big);    // Wrong
```

## Phase 5: Systematic Debugging Steps

### 5.1 Add Comprehensive Logging
Insert debug logs to trace:
```dart
print('TTS chunk received: ${chunkData.length} bytes, chunk #${chunkNumber}');
print('Audio buffer size: ${audioBuffer.length}');
print('Audio player state: ${audioPlayer.state}');
print('First 10 bytes: ${chunkData.take(10).toList()}');
```

### 5.2 Audio Data Validation
```dart
// Validate chunk data
void validateAudioChunk(List<int> chunk) {
  // Check for valid int16 range (-32768 to 32767)
  for (int i = 0; i < chunk.length; i += 2) {
    if (i + 1 < chunk.length) {
      int value = (chunk[i + 1] << 8) | chunk[i]; // Little-endian
      if (value > 32767) value -= 65536; // Convert to signed
      if (value < -32768 || value > 32767) {
        print('Invalid audio sample at position $i: $value');
      }
    }
  }
}
```

### 5.3 Incremental Testing
1. **Test single chunk**: Send one chunk, verify playback
2. **Test chunk ordering**: Log chunk numbers, check sequence
3. **Test timing**: Remove delays, add delays
4. **Test formats**: Save chunks as files, play externally

## Phase 6: Common Solutions to Implement

### 6.1 Audio Format Alignment
```dart
// Ensure correct format
final AudioSource audioSource = AudioSource.bytes(
  audioBytes,
  format: AudioFormat(
    sampleRate: 22050,
    channels: 1,
    bitDepth: 16,
    encoding: AudioEncoding.pcm,
  ),
);
```

### 6.2 Proper Chunk Buffering
```dart
class AudioChunkBuffer {
  final List<Uint8List> _chunks = [];
  final StreamController<Uint8List> _controller = StreamController();
  
  void addChunk(List<int> chunk) {
    final uint8Chunk = Uint8List.fromList(chunk);
    _chunks.add(uint8Chunk);
    _controller.add(uint8Chunk);
  }
  
  Stream<Uint8List> get stream => _controller.stream;
}
```

### 6.3 Error Recovery
```dart
// Add timeout and retry logic
Timer? chunkTimeout;

void onTTSChunk(dynamic data) {
  chunkTimeout?.cancel();
  
  try {
    // Process chunk
    processAudioChunk(data);
  } catch (e) {
    print('Error processing chunk: $e');
    // Request chunk retry or reset
  }
  
  // Set timeout for next chunk
  chunkTimeout = Timer(Duration(milliseconds: 100), () {
    print('Chunk timeout - possible connection issue');
  });
}
```

## Phase 7: Testing & Validation

### 7.1 Audio File Output Test
```dart
// Save received chunks as WAV file for external validation
File audioFile = File('debug_output.wav');
IOSink sink = audioFile.openWrite();

// WAV header for 22050 Hz, 16-bit, mono
List<int> wavHeader = createWavHeader(totalBytes: estimatedSize);
sink.add(wavHeader);

// Add all chunks
for (var chunk in receivedChunks) {
  sink.add(chunk);
}
await sink.close();
```

### 7.2 Cross-Platform Testing
- Test on iOS vs Android
- Test on physical device vs simulator
- Test different audio output routes (speaker, headphones)

## Phase 8: Performance Optimization

### 8.1 Memory Management
```dart
// Use circular buffer for large streams
class CircularAudioBuffer {
  final int maxSize;
  final Uint8List _buffer;
  int _writePos = 0;
  int _readPos = 0;
  
  CircularAudioBuffer(this.maxSize) : _buffer = Uint8List(maxSize);
  
  bool write(Uint8List data) {
    // Implement circular write with overflow handling
  }
}
```

### 8.2 Chunk Size Optimization
- Test different chunk sizes (512, 1024, 2048 bytes)
- Measure latency vs quality tradeoffs
- Adjust based on device capabilities

## Files to Prioritize for LLM Search

1. **SocketIO client setup** - Connection and event handling
2. **TTS event handlers** - Chunk reception and processing  
3. **Audio player implementation** - Playback and streaming
4. **Audio buffer management** - Data accumulation and flow
5. **Main app state** - Overall audio flow coordination

## Search Queries for LLM

```bash
# Primary searches
"tts_audio_chunk" AND ("socket" OR "socketio")
"audio" AND ("player" OR "stream") AND "chunk"
"Uint8List" AND "audio" 
"sample_rate" OR "sampleRate" AND "22050"

# Secondary searches
"ByteData" AND ("getInt16" OR "setInt16")
"AudioSource" OR "AudioPlayer" configuration
"StreamController" AND "audio"
"Timer" AND ("audio" OR "chunk")
```

This systematic approach should help identify whether the issue is in data reception, format conversion, buffering, or audio playback. 