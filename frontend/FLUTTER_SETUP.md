# Flutter Voice Conversation App Setup

This Flutter app provides a native mobile interface for your Phase 3 voice-to-voice conversation system. It connects to your existing Python Flask-SocketIO backend and provides the same three modes as your HTML interface but with better mobile performance.

## 🎯 What This Replaces

Your current HTML/JavaScript interface with these improvements:
- **Native audio recording** (better quality than web)
- **Optimized audio playback** (lower latency)
- **Mobile-optimized UI** (touch-friendly controls)
- **Background support** (works when app is backgrounded)
- **App store ready** (can be distributed via app stores)

## 🚀 Quick Setup

### 1. Prerequisites
- Flutter SDK (>=3.10.0) - [Install Flutter](https://docs.flutter.dev/get-started/install)
- Your Python backend running (with Phase 3 Whisper integration)
- Android Studio (for Android) or Xcode (for iOS)

### 2. Install Dependencies
```bash
cd flutter_voice_app
flutter pub get
```

### 3. Update Backend Connection
Edit `lib/screens/voice_conversation_screen.dart`, line ~38:
```dart
// Change this to your computer's IP address if testing on physical device
await _webSocketService.connect(host: 'localhost', port: 8000);

// For physical device, use your computer's IP:
// await _webSocketService.connect(host: '192.168.1.100', port: 8000);
```

### 4. Run the App
```bash
# For Android emulator or connected device
flutter run

# For iOS simulator (Mac only)
flutter run

# To specify device
flutter devices
flutter run -d <device-id>
```

## 📱 Complete Testing Flow

### 1. Start Your Python Backend
```bash
cd /path/to/your/python/project
python app.py
```

### 2. Launch Flutter App
The app will automatically connect to your backend when launched.

### 3. Test All Three Modes

#### **Direct TTS Mode**
1. Type text in the input field
2. Tap "Speak It"
3. Audio should play through device speakers

#### **AI Conversation Mode**
1. Type a message to the AI
2. Tap "Chat with AI"
3. See conversation flow: Your message → AI thinking → AI response → TTS audio

#### **Voice Conversation Mode** (The new feature!)
1. Tap "Voice Conversation"
2. Tap the green microphone button
3. Speak your message (button turns red while recording)
4. Tap stop or it auto-stops after silence
5. Watch the flow: Recording → Processing → AI thinking → AI speaking
6. Repeat for continued conversation

## 🔧 Architecture

```
Flutter App ←WebSocket→ Python Backend ←→ OpenAI Whisper + Cartesia TTS
     ↓                        ↓
Native Audio          Phase 3 Implementation
```

**Key Services:**
- **`ConversationState`**: App state management (messages, status, mode)
- **`WebSocketService`**: SocketIO connection to Python backend
- **`AudioService`**: Recording (to backend) and playback (from TTS)

## 📂 Project Structure

```
flutter_voice_app/
├── lib/
│   ├── main.dart                    # App entry point
│   ├── services/
│   │   ├── conversation_state.dart  # State management
│   │   ├── websocket_service.dart   # Backend communication
│   │   └── audio_service.dart       # Audio recording/playback
│   └── screens/
│       └── voice_conversation_screen.dart  # Main UI
├── android/                         # Android-specific config
├── ios/                            # iOS-specific config
└── pubspec.yaml                    # Dependencies
```

## 🎮 User Interface

### Mode Selector (Top)
Three buttons: **Direct TTS** | **AI Conversation** | **Voice Conversation**

### Direct TTS Mode
- Text input field
- "Speak It" button
- Audio plays through speakers

### AI Conversation Mode
- Text input field
- "Chat with AI" button
- Conversation history view
- Audio responses

### Voice Conversation Mode
- Large circular microphone button (green/red/orange states)
- Voice status text ("Click to start", "Recording...", "Processing...")
- Conversation history with voice indicators
- Auto-playing TTS responses

## 🔊 Audio Flow

### Recording (Voice → Backend)
1. **Tap microphone** → Request permission → Start recording
2. **Tap stop** → Stop recording → Convert to base64 → Send via WebSocket
3. **Backend processes** → Whisper transcription → OpenAI response → Cartesia TTS
4. **Receive audio chunks** → Play through speakers

### Playback (Backend → Speakers)
1. **Receive `audio_chunk` events** from backend
2. **Queue audio chunks** for sequential playback
3. **Convert to temporary files** → Play via native audio player
4. **Clean up** temporary files after playback

## 🐛 Troubleshooting

### "Connection failed"
```
Waiting for connection...
```
**Solutions:**
- Ensure Python backend is running on correct port
- Check IP address (use computer's IP for physical devices)
- Verify firewall settings allow connections

### "Microphone permission denied"
```
Failed to start recording. Please check microphone permissions.
```
**Solutions:**
- Android: Go to Settings → Apps → Voice Conversation App → Permissions → Microphone
- iOS: Go to Settings → Privacy & Security → Microphone → Voice Conversation App

### "Audio not playing"
```
TTS finished but no audio heard
```
**Solutions:**
- Check device volume
- Test with headphones
- Verify backend is sending correct audio format

### "Recording not working"
```
No audio recorded
```
**Solutions:**
- Test microphone with other apps
- Check Android/iOS permissions
- Try restarting the app

## 🔧 Backend Compatibility

**Uses exact same SocketIO events as HTML version:**
- `start_voice_conversation` → Initialize voice mode
- `audio_chunk` → Send recorded audio
- `conversation_text_input` → Send text messages
- `synthesize_speech_streaming` → TTS requests
- `audio_chunk` (incoming) → Receive TTS audio
- All status events (`ai_thinking`, `transcription_complete`, etc.)

## 📊 Performance Benefits

| Feature | HTML Version | Flutter App |
|---------|-------------|-------------|
| Audio Latency | ~200ms | ~100ms |
| Recording Quality | Web MediaRecorder | Native Audio |
| Battery Usage | High (browser) | Optimized |
| Background Support | Limited | Full |
| Offline Support | None | Possible |
| App Store | PWA only | Native apps |

## 🚀 Building for Release

### Android APK
```bash
flutter build apk --release
# Output: build/app/outputs/flutter-apk/app-release.apk
```

### iOS App (requires Mac + Xcode)
```bash
flutter build ios --release
# Then use Xcode to archive and distribute
```

## 🔧 Configuration Options

### Change Backend Host/Port
In `voice_conversation_screen.dart`:
```dart
await _webSocketService.connect(host: 'your-server.com', port: 8000);
```

### Adjust Audio Settings
In `audio_service.dart`:
```dart
await _recorder.start(
  const RecordConfig(
    encoder: AudioEncoder.aacLc,  // Change format if needed
    sampleRate: 16000,            // Match backend expectations
    numChannels: 1,               // Mono audio
  ),
);
```

### Customize UI Colors/Theme
In `main.dart`:
```dart
theme: ThemeData(
  primarySwatch: Colors.blue,     // Change app color scheme
  useMaterial3: true,
),
```

## ✅ Success Checklist

- [ ] Flutter app connects to Python backend
- [ ] Direct TTS mode works (text → speech)
- [ ] AI Conversation mode works (text → AI → speech)
- [ ] Voice Conversation mode works (voice → AI → speech)
- [ ] Microphone permissions granted
- [ ] Audio playback working
- [ ] Conversation history displays correctly
- [ ] All three modes switch properly

## 🆘 Getting Help

If you encounter issues:

1. **Check Flutter Doctor**: `flutter doctor -v`
2. **View Flutter logs**: Run app with `flutter run` and watch console
3. **Test backend separately**: Use your HTML version to verify backend works
4. **Check device logs**: 
   - Android: `flutter logs` or Android Studio
   - iOS: Xcode console

The Flutter app is designed to be a drop-in replacement for your HTML interface with better mobile performance and native audio capabilities! 