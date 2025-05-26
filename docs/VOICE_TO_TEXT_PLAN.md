# Voice-to-Text Integration Plan

## Overview
Integrate OpenAI Whisper for voice-to-text transcription that feeds into the existing ChatGPT conversation pipeline, creating a complete voice conversation system.

## Architecture

```
[User Voice Input] 
    ↓ (Flutter Audio Recording)
[Frontend Audio Capture] 
    ↓ (WebSocket: voice_data event)
[Backend Audio Processing] 
    ↓ (Whisper API)
[Text Transcription] 
    ↓ (Existing Pipeline)
[ChatGPT Processing] 
    ↓ (Existing Pipeline)
[TTS Audio Response] 
    ↓ (Existing Pipeline)
[Frontend Audio Playback]
```

## Implementation Phases

### Phase 1: Backend Voice Processing Service

#### 1.1 Create Whisper Integration Service
**File:** `backend/services/whisper_handler.py`

**Features:**
- OpenAI Whisper API integration
- Audio format validation and conversion
- Chunked audio processing for real-time transcription
- Error handling and retry logic
- Support for multiple audio formats (WAV, MP3, M4A, etc.)

**Key Functions:**
```python
def transcribe_audio(audio_data: bytes, format: str = 'wav') -> str
def transcribe_audio_stream(audio_chunks: Iterator[bytes]) -> Iterator[str]
def validate_audio_format(audio_data: bytes) -> bool
```

#### 1.2 WebSocket Voice Events Handler
**File:** `backend/websocket/voice_events.py` (enhance existing)

**New Events:**
- `start_voice_recording` - Initialize voice recording session
- `voice_chunk` - Receive audio chunks for real-time processing
- `stop_voice_recording` - Finalize recording and process
- `voice_data` - Complete audio file processing (existing, enhance)

**Response Events:**
- `transcription_partial` - Partial transcription results (real-time)
- `transcription_complete` - Final transcription result
- `transcription_error` - Error in voice processing

#### 1.3 Audio Processing Pipeline
**Features:**
- Audio format detection and conversion
- Noise reduction (optional)
- Voice activity detection (VAD)
- Audio chunking for streaming transcription
- Temporary file management

### Phase 2: Frontend Voice Capture

#### 2.1 Voice Recording Service
**File:** `frontend/lib/services/voice_recording_service.dart`

**Features:**
- Microphone permission handling
- Real-time audio recording
- Audio format configuration (WAV, 16kHz, mono)
- Voice activity detection (start/stop recording automatically)
- Audio level monitoring
- Chunked streaming to backend

**Key Methods:**
```dart
Future<void> startRecording()
Future<void> stopRecording()
Stream<Uint8List> getAudioStream()
Future<bool> requestPermissions()
```

#### 2.2 Voice UI Components
**Files:** 
- `frontend/lib/widgets/voice_input_button.dart`
- `frontend/lib/widgets/voice_recording_indicator.dart`

**Features:**
- Push-to-talk button
- Voice level indicator
- Recording status display
- Transcription preview
- Error state handling

#### 2.3 Enhanced WebSocket Integration
**File:** `frontend/lib/services/websocket_service.dart` (enhance existing)

**New Methods:**
```dart
void startVoiceRecording()
void sendVoiceChunk(Uint8List audioData)
void stopVoiceRecording()
void setOnTranscriptionReceived(Function(String) callback)
```

### Phase 3: Integration with Existing Chat Pipeline

#### 3.1 Conversation Flow Integration
**File:** `backend/websocket/conversation_events.py` (enhance existing)

**Integration Points:**
- Route transcribed text through existing `_process_transcribed_text_as_conversation()`
- Add voice source indicators to conversation history
- Handle voice-specific error cases
- Maintain conversation context across voice and text inputs

#### 3.2 Enhanced Response Handling
**Features:**
- Automatic TTS for voice-initiated conversations
- Voice conversation mode detection
- Mixed input handling (voice + text in same conversation)
- Conversation source tracking

### Phase 4: Advanced Features

#### 4.1 Real-time Streaming Transcription
**Features:**
- Continuous voice recognition
- Partial result updates
- Voice command detection
- Interrupt handling

#### 4.2 Voice Activity Detection (VAD)
**Features:**
- Automatic start/stop recording
- Silence detection
- Background noise filtering
- Speech endpoint detection

#### 4.3 Multi-language Support
**Features:**
- Language detection
- Multi-language transcription
- Language-specific TTS responses

## Technical Specifications

### Audio Requirements
- **Sample Rate:** 16kHz (Whisper optimal)
- **Channels:** Mono
- **Format:** WAV/PCM for processing, compressed for transmission
- **Chunk Size:** 1-3 seconds for real-time processing
- **Max Duration:** 30 seconds per chunk (Whisper limit)

### API Integration
- **Whisper Model:** `whisper-1` (OpenAI API)
- **Fallback:** Local Whisper model for offline capability
- **Rate Limiting:** Handle API rate limits gracefully
- **Cost Optimization:** Chunk audio efficiently

### Performance Targets
- **Transcription Latency:** < 2 seconds for 5-second audio
- **Real-time Factor:** < 0.5x (process faster than real-time)
- **Accuracy:** > 95% for clear speech
- **Memory Usage:** < 100MB additional for voice processing

## Implementation Timeline

### Week 1: Backend Foundation
- [ ] Create `whisper_handler.py` service
- [ ] Enhance `voice_events.py` with new events
- [ ] Add audio processing utilities
- [ ] Create voice processing tests

### Week 2: Frontend Voice Capture
- [ ] Implement `voice_recording_service.dart`
- [ ] Create voice UI components
- [ ] Add microphone permissions
- [ ] Integrate with WebSocket service

### Week 3: Pipeline Integration
- [ ] Connect voice transcription to chat pipeline
- [ ] Add conversation flow enhancements
- [ ] Implement error handling
- [ ] Create end-to-end tests

### Week 4: Polish & Advanced Features
- [ ] Add real-time streaming transcription
- [ ] Implement voice activity detection
- [ ] Performance optimization
- [ ] Documentation and final testing

## Testing Strategy

### Unit Tests
- Whisper API integration tests
- Audio format validation tests
- WebSocket event handling tests
- Voice recording service tests

### Integration Tests
- End-to-end voice conversation tests
- Mixed input (voice + text) tests
- Error scenario tests
- Performance benchmarks

### Manual Testing
- Voice quality in different environments
- Multiple device testing
- Network condition testing
- User experience testing

## Dependencies

### Backend
```python
# Add to requirements.txt
openai>=1.3.7  # Already included
pydub>=0.25.1  # Already included
speech-recognition>=3.10.0  # For VAD
webrtcvad>=2.0.10  # Voice activity detection
```

### Frontend
```yaml
# Add to pubspec.yaml
record: ^5.0.0  # Audio recording
permission_handler: ^11.0.0  # Microphone permissions
path_provider: ^2.1.0  # File storage
```

## Security Considerations

### Privacy
- Audio data encryption in transit
- Temporary file cleanup
- No persistent audio storage
- User consent for voice recording

### API Security
- Rate limiting implementation
- API key protection
- Error message sanitization
- Audit logging for voice processing

## Monitoring & Analytics

### Metrics to Track
- Transcription accuracy rates
- Processing latency
- API usage and costs
- Error rates by audio quality
- User engagement with voice features

### Logging
- Voice processing events
- Transcription results (anonymized)
- Performance metrics
- Error conditions

## Future Enhancements

### Advanced Features
- Speaker identification
- Emotion detection in voice
- Voice command shortcuts
- Custom wake words
- Offline transcription capability

### Optimization
- Edge computing for transcription
- Custom Whisper model fine-tuning
- Audio compression optimization
- Caching strategies

## Success Criteria

### Functional
- [ ] Users can speak and receive text transcription
- [ ] Transcribed text flows into ChatGPT conversation
- [ ] Voice conversations work end-to-end
- [ ] Error handling works gracefully

### Performance
- [ ] < 2 second transcription latency
- [ ] > 95% transcription accuracy for clear speech
- [ ] Stable performance across devices
- [ ] Minimal impact on app performance

### User Experience
- [ ] Intuitive voice input interface
- [ ] Clear feedback during recording
- [ ] Seamless transition between voice and text
- [ ] Reliable voice activity detection 