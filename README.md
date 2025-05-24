# Voice Agent - AI Voice Conversation System

A complete voice-to-voice AI conversation system with Flutter frontend and Python backend.

## 🎯 Features

- **Direct Text-to-Speech**: Convert text to natural speech using Cartesia TTS
- **AI Conversation**: Chat with OpenAI GPT models via text
- **Voice Conversation**: Complete voice-to-voice AI interaction using Whisper + GPT + TTS
- **Real-time Audio Streaming**: Low-latency audio processing and playback
- **Cross-platform Mobile App**: Flutter app for iOS and Android

## 🏗️ Architecture

```
┌─────────────────┐    WebSocket    ┌─────────────────┐
│  Flutter App    │ ◄──────────────► │  Python Backend │
│  (Frontend)     │                  │  (Flask-SocketIO)│
└─────────────────┘                  └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   External APIs │
                                    │ • OpenAI Whisper│
                                    │ • OpenAI GPT    │
                                    │ • Cartesia TTS  │
                                    └─────────────────┘
```

## 📁 Project Structure

```
voice_agent/
├── backend/                    # Python Flask-SocketIO backend
│   ├── app.py                 # Main application entry point
│   ├── requirements.txt       # Python dependencies
│   ├── services/              # Core business logic
│   ├── websocket/             # WebSocket event handlers
│   ├── config/                # Configuration management
│   └── temp_audio/            # Temporary audio files
├── frontend/                  # Flutter mobile application
│   ├── lib/                   # Flutter source code
│   ├── android/               # Android configuration
│   └── ios/                   # iOS configuration
├── scripts/                   # Utility scripts
│   ├── run_backend.sh         # Start backend server
│   └── run_frontend.sh        # Start Flutter app
└── docs/                      # Documentation
```

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** with pip
- **Flutter 3.0+** with Dart SDK
- **OpenAI API Key** (for Whisper and GPT)
- **Cartesia API Key** (for TTS)

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env and add your API keys

# Run the backend
python app.py
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Get Flutter dependencies
flutter pub get

# Run the app (with device connected)
flutter run
```

### 3. Using Utility Scripts

```bash
# Start backend (from project root)
./scripts/run_backend.sh

# Start frontend (from project root)
./scripts/run_frontend.sh
```

## 🔧 Configuration

### Backend Configuration

Create a `.env` file in the `backend/` directory:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
CARTESIA_API_KEY=your_cartesia_api_key_here

# Optional
HOST=0.0.0.0
PORT=8000
DEBUG=true
```

### Frontend Configuration

The Flutter app automatically connects to `localhost:8000`. To change this, edit:
- `frontend/lib/services/websocket_service.dart`

## 🎮 Usage

1. **Start the backend server** using the script or manually
2. **Launch the Flutter app** on your device/emulator
3. **Choose a mode**:
   - **Direct TTS**: Type text and hear it spoken
   - **AI Conversation**: Chat with AI via text
   - **Voice Conversation**: Speak to AI and hear responses

## 🔊 Voice Conversation Flow

1. User taps microphone button to start recording
2. Audio is captured and sent to backend
3. Backend transcribes audio using OpenAI Whisper
4. Transcribed text is sent to OpenAI GPT for response
5. AI response is converted to speech using Cartesia TTS
6. Audio is streamed back to Flutter app and played

## 🛠️ Development

### Backend Development

```bash
cd backend
source venv/bin/activate
python app.py
```

The backend runs on `http://localhost:8000` with WebSocket support.

### Frontend Development

```bash
cd frontend
flutter run
```

Hot reload is enabled for rapid development.

### Testing

```bash
# Backend tests
cd backend
python -m pytest tests/

# Frontend tests
cd frontend
flutter test
```

## 📱 Mobile App Features

- **Three conversation modes** with clear UI
- **Real-time audio recording** with visual feedback
- **Conversation history** with message bubbles
- **Connection status** indicators
- **Error handling** with user-friendly messages
- **Responsive design** for different screen sizes

## 🔌 API Integration

### OpenAI Integration
- **Whisper**: Speech-to-text transcription
- **GPT-3.5/4**: Conversational AI responses

### Cartesia Integration
- **Real-time TTS**: High-quality voice synthesis
- **Streaming audio**: Low-latency audio delivery

## 🚀 Deployment

### Backend Deployment
- Deploy to cloud platforms (AWS, GCP, Azure)
- Use Docker for containerization
- Configure environment variables for production

### Frontend Deployment
- Build APK/IPA for app stores
- Configure production backend URLs
- Handle app store requirements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the documentation in `docs/`
2. Review existing GitHub issues
3. Create a new issue with detailed information

## 🔄 Migration from Old Structure

This project has been restructured for better maintainability. Old files are preserved in the `deprecated/` directory during the transition period. 