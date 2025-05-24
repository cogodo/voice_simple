# Troubleshooting Guide

## 🐛 Common Issues and Solutions

### **1. Dependency Conflicts**

#### Problem:
```
ERROR: Cannot install -r backend/requirements.txt (line 3) and python-engineio==4.7.1 because these package versions have conflicting dependencies.
```

#### Solution:
Update `backend/requirements.txt` with compatible versions:
```txt
# ✅ Compatible versions
python-socketio==5.10.0
python-engineio==4.9.0  # Must be >=4.8.0 for socketio 5.10.0
```

#### Prevention:
Always check package compatibility when updating versions. Use `pip check` after installation.

### **2. Import Errors in Backend**

#### Problem:
```
ImportError: attempted relative import beyond top-level package
```

#### Cause:
Using relative imports (`from ..services.module`) when running Python from the `backend/` directory.

#### Solution:
Use absolute imports in all modules:
```python
# ❌ Relative imports (cause issues)
from ..services.whisper_handler import transcribe_audio

# ✅ Absolute imports (work correctly)
from services.whisper_handler import transcribe_audio
```

### **3. Missing Environment Variables**

#### Problem:
```
WARNING: OPENAI_API_KEY environment variable is not set
```

#### Solution:
1. Create `.env` file in `backend/` directory:
   ```bash
   cd backend
   cp .env.example .env
   ```

2. Add your API keys:
   ```env
   OPENAI_API_KEY=your_key_here
   CARTESIA_API_KEY=your_key_here
   ```

### **4. Flutter Dependencies**

#### Problem:
```
flutter pub get fails
```

#### Solution:
```bash
cd frontend
flutter clean
flutter pub get
```

If still failing, check Flutter installation:
```bash
flutter doctor
```

### **5. Audio Permissions (Mobile)**

#### Problem:
Voice recording not working on mobile devices.

#### Solution:
Ensure permissions are properly configured:

**Android** (`frontend/android/app/src/main/AndroidManifest.xml`):
```xml
<uses-permission android:name="android.permission.RECORD_AUDIO" />
```

**iOS** (`frontend/ios/Runner/Info.plist`):
```xml
<key>NSMicrophoneUsageDescription</key>
<string>This app needs microphone access for voice conversation</string>
```

### **6. WebSocket Connection Issues**

#### Problem:
Flutter app can't connect to backend.

#### Solutions:

1. **Check backend is running:**
   ```bash
   cd backend
   python3 app.py
   ```

2. **Check connection URL in Flutter:**
   Edit `frontend/lib/services/websocket_service.dart`:
   ```dart
   // For local development
   static const String serverUrl = 'http://localhost:8000';
   
   // For device testing (replace with your IP)
   static const String serverUrl = 'http://192.168.1.100:8000';
   ```

3. **Firewall issues:**
   Make sure port 8000 is open for local connections.

## 🔧 **Verification Commands**

### Backend Health Check:
```bash
cd backend
python3 -c "from app import create_app; print('✅ Backend OK')"
```

### Frontend Health Check:
```bash
cd frontend
flutter analyze lib/core/constants.dart
```

### Full System Check:
```bash
# From project root
./scripts/run_backend.sh &  # Start backend in background
./scripts/run_frontend.sh   # Start frontend
```

## 📞 **Getting Help**

If you encounter issues not covered here:

1. Check the logs for specific error messages
2. Verify all dependencies are installed correctly
3. Ensure environment variables are set
4. Check that ports are not in use by other applications
5. Review the project documentation in `docs/`

## 🐞 **Debug Mode**

Enable debug logging:

**Backend:**
```python
# In backend/.env
DEBUG=true
```

**Flutter:**
```bash
flutter run --debug
``` 