#!/usr/bin/env python3
"""
Deep diagnostic tests for LLM initialization and voice transcription issues.
"""
import sys
import os
import time
import requests
from unittest.mock import Mock

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class DeepDiagnostics:
    def __init__(self):
        self.test_results = {}
        self.issues_found = []
        
    def test_environment_variables(self):
        """Test that required environment variables are set."""
        print("🧪 Test 1: Environment Variables")
        
        required_vars = [
            'OPENAI_API_KEY',
            'CARTESIA_API_KEY'
        ]
        
        missing_vars = []
        
        for var in required_vars:
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                print(f"   ❌ {var}: NOT SET")
            elif value.startswith('sk-') or len(value) > 10:
                print(f"   ✅ {var}: SET (length: {len(value)})")
            else:
                print(f"   ⚠️  {var}: SET but looks suspicious (length: {len(value)})")
        
        if missing_vars:
            self.issues_found.append(f"Missing environment variables: {', '.join(missing_vars)}")
        
        success = len(missing_vars) == 0
        self.test_results['environment'] = success
        
        if success:
            print("   ✅ Environment Variables test PASSED")
        else:
            print("   ❌ Environment Variables test FAILED")
            print("   💡 Fix: Set missing environment variables in .env file")
        
        return success
    
    def test_openai_initialization(self):
        """Test OpenAI client initialization and basic functionality."""
        print("\n🧪 Test 2: OpenAI Initialization")
        
        try:
            from services.openai_handler import create_conversation_manager
            
            # Test creation
            print("   🔧 Creating conversation manager...")
            mock_logger = Mock()
            conversation_manager = create_conversation_manager(mock_logger)
            
            if conversation_manager is None:
                print("   ❌ Conversation manager creation returned None")
                self.issues_found.append("OpenAI conversation manager creation failed")
                success = False
            else:
                print("   ✅ Conversation manager created successfully")
                
                # Test basic functionality
                print("   🔧 Testing basic conversation functionality...")
                try:
                    # Test adding a message
                    conversation_manager.add_user_message("Hello")
                    print("   ✅ Can add user messages")
                    
                    # Test getting response (with timeout)
                    print("   🔧 Testing AI response generation (this may take a few seconds)...")
                    start_time = time.time()
                    response = conversation_manager.get_response("Say 'test response'")
                    end_time = time.time()
                    
                    if response and len(response.strip()) > 0:
                        print(f"   ✅ AI response generated in {end_time - start_time:.1f}s")
                        print(f"   📝 Response: '{response[:100]}{'...' if len(response) > 100 else ''}'")
                        success = True
                    else:
                        print("   ❌ AI response was empty or None")
                        self.issues_found.append("OpenAI API returns empty responses")
                        success = False
                        
                except Exception as e:
                    print(f"   ❌ Error testing conversation functionality: {e}")
                    self.issues_found.append(f"OpenAI API error: {str(e)}")
                    success = False
                    
        except ImportError as e:
            print(f"   ❌ Cannot import OpenAI handler: {e}")
            self.issues_found.append(f"OpenAI import error: {str(e)}")
            success = False
        except Exception as e:
            print(f"   ❌ OpenAI initialization error: {e}")
            self.issues_found.append(f"OpenAI initialization error: {str(e)}")
            success = False
        
        self.test_results['openai'] = success
        
        if success:
            print("   ✅ OpenAI Initialization test PASSED")
        else:
            print("   ❌ OpenAI Initialization test FAILED")
            print("   💡 Fix: Check API key, network connection, and OpenAI service status")
        
        return success
    
    def test_whisper_initialization(self):
        """Test Whisper handler initialization."""
        print("\n🧪 Test 3: Whisper Initialization")
        
        try:
            from services.whisper_handler import create_whisper_handler
            
            print("   🔧 Creating Whisper handler...")
            mock_logger = Mock()
            whisper_handler = create_whisper_handler(mock_logger)
            
            if whisper_handler is None:
                print("   ❌ Whisper handler creation returned None")
                self.issues_found.append("Whisper handler creation failed")
                success = False
            else:
                print("   ✅ Whisper handler created successfully")
                
                # Test basic functionality
                print("   🔧 Testing Whisper handler methods...")
                try:
                    # Test if we can validate audio format
                    test_audio = b'\x00' * 1000  # Dummy audio data
                    can_validate = hasattr(whisper_handler, 'validate_audio_format')
                    can_transcribe = hasattr(whisper_handler, 'transcribe_audio')
                    can_get_info = hasattr(whisper_handler, 'get_audio_info')
                    
                    print(f"   📊 Has validate_audio_format: {'✅' if can_validate else '❌'}")
                    print(f"   📊 Has transcribe_audio: {'✅' if can_transcribe else '❌'}")
                    print(f"   📊 Has get_audio_info: {'✅' if can_get_info else '❌'}")
                    
                    success = can_validate and can_transcribe and can_get_info
                    
                    if not success:
                        self.issues_found.append("Whisper handler missing required methods")
                        
                except Exception as e:
                    print(f"   ❌ Error testing Whisper methods: {e}")
                    self.issues_found.append(f"Whisper method error: {str(e)}")
                    success = False
                    
        except ImportError as e:
            print(f"   ❌ Cannot import Whisper handler: {e}")
            self.issues_found.append(f"Whisper import error: {str(e)}")
            success = False
        except Exception as e:
            print(f"   ❌ Whisper initialization error: {e}")
            self.issues_found.append(f"Whisper initialization error: {str(e)}")
            success = False
        
        self.test_results['whisper'] = success
        
        if success:
            print("   ✅ Whisper Initialization test PASSED")
        else:
            print("   ❌ Whisper Initialization test FAILED")
            print("   💡 Fix: Check Whisper dependencies and configuration")
        
        return success
    
    def test_voice_synthesis_initialization(self):
        """Test voice synthesis (Cartesia) initialization."""
        print("\n🧪 Test 4: Voice Synthesis Initialization")
        
        try:
            from services.voice_synthesis import my_processing_function_streaming
            
            print("   ✅ Voice synthesis import successful")
            
            # Test if function is callable
            if callable(my_processing_function_streaming):
                print("   ✅ Voice synthesis function is callable")
                success = True
            else:
                print("   ❌ Voice synthesis function is not callable")
                self.issues_found.append("Voice synthesis function not callable")
                success = False
                
        except ImportError as e:
            print(f"   ❌ Cannot import voice synthesis: {e}")
            self.issues_found.append(f"Voice synthesis import error: {str(e)}")
            success = False
        except Exception as e:
            print(f"   ❌ Voice synthesis error: {e}")
            self.issues_found.append(f"Voice synthesis error: {str(e)}")
            success = False
        
        self.test_results['voice_synthesis'] = success
        
        if success:
            print("   ✅ Voice Synthesis Initialization test PASSED")
        else:
            print("   ❌ Voice Synthesis Initialization test FAILED")
            print("   💡 Fix: Check Cartesia API key and dependencies")
        
        return success
    
    def test_dependencies(self):
        """Test that all required Python packages are installed."""
        print("\n🧪 Test 5: Python Dependencies")
        
        required_packages = [
            'openai',
            'cartesia', 
            'flask',
            'flask_socketio',
            'socketio',  # python-socketio is imported as 'socketio'
            'requests',
            'pydub'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"   ✅ {package}: INSTALLED")
            except ImportError:
                missing_packages.append(package)
                print(f"   ❌ {package}: NOT INSTALLED")
        
        if missing_packages:
            self.issues_found.append(f"Missing packages: {', '.join(missing_packages)}")
        
        success = len(missing_packages) == 0
        self.test_results['dependencies'] = success
        
        if success:
            print("   ✅ Dependencies test PASSED")
        else:
            print("   ❌ Dependencies test FAILED")
            print(f"   💡 Fix: Install missing packages with: uv pip install {' '.join(missing_packages)}")
        
        return success
    
    def test_server_websocket_functionality(self):
        """Test server WebSocket event registration."""
        print("\n🧪 Test 6: Server WebSocket Functionality")
        
        try:
            # Test that we can register all event handlers without errors
            from flask import Flask
            from flask_socketio import SocketIO
            
            app = Flask(__name__)
            app.logger = Mock()
            socketio = SocketIO()
            
            # Test conversation events
            from websocket.conversation_events import register_conversation_events
            register_conversation_events(socketio, app)
            print("   ✅ Conversation events registered")
            
            # Test voice events  
            from websocket.voice_events import register_voice_events
            voice_sessions = {}
            register_voice_events(socketio, app, voice_sessions)
            print("   ✅ Voice events registered")
            
            # Test TTS events
            from websocket.tts_events import register_tts_events
            register_tts_events(socketio, app)
            print("   ✅ TTS events registered")
            
            success = True
            
        except Exception as e:
            print(f"   ❌ WebSocket registration error: {e}")
            self.issues_found.append(f"WebSocket registration error: {str(e)}")
            success = False
        
        self.test_results['websocket'] = success
        
        if success:
            print("   ✅ Server WebSocket Functionality test PASSED")
        else:
            print("   ❌ Server WebSocket Functionality test FAILED")
            print("   💡 Fix: Check WebSocket event handler code for errors")
        
        return success
    
    def generate_diagnostics_report(self):
        """Generate a comprehensive diagnostics report."""
        print("\n" + "=" * 80)
        print("🔍 DEEP DIAGNOSTICS REPORT")
        print("=" * 80)
        
        # Summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        
        print(f"📊 Tests Passed: {passed_tests}/{total_tests}")
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name}: {status}")
        
        # Issues found
        if self.issues_found:
            print(f"\n🚨 ISSUES DETECTED ({len(self.issues_found)}):")
            for i, issue in enumerate(self.issues_found, 1):
                print(f"   {i}. {issue}")
        else:
            print("\n✅ NO ISSUES DETECTED")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if not self.test_results.get('environment', True):
            print("   🔧 Set up environment variables in .env file")
            print("      - OPENAI_API_KEY=your_openai_key")
            print("      - CARTESIA_API_KEY=your_cartesia_key")
        
        if not self.test_results.get('dependencies', True):
            print("   🔧 Install missing dependencies:")
            print("      uv pip install openai cartesia flask flask-socketio")
        
        if not self.test_results.get('openai', True):
            print("   🔧 Fix OpenAI issues:")
            print("      - Verify API key is valid")
            print("      - Check network connectivity")
            print("      - Test OpenAI service status")
        
        if not self.test_results.get('whisper', True):
            print("   🔧 Fix Whisper issues:")
            print("      - Check Whisper model availability")
            print("      - Verify audio processing dependencies")
        
        if not self.test_results.get('voice_synthesis', True):
            print("   🔧 Fix Voice Synthesis issues:")
            print("      - Verify Cartesia API key")
            print("      - Check audio output configuration")
        
        # Overall status
        all_critical_passed = (
            self.test_results.get('environment', False) and
            self.test_results.get('openai', False) and
            self.test_results.get('whisper', False) and
            self.test_results.get('dependencies', False)
        )
        
        print(f"\n🎯 OVERALL STATUS:")
        if all_critical_passed:
            print("   🎉 ALL CRITICAL SYSTEMS OPERATIONAL")
            print("   🚀 Ready for voice agent functionality")
        else:
            print("   ⚠️  CRITICAL ISSUES NEED ATTENTION")
            print("   🔧 Fix issues above before testing voice features")
        
        return all_critical_passed
    
    def run_all_diagnostics(self):
        """Run all diagnostic tests."""
        print("🔍 DEEP DIAGNOSTIC TEST SUITE")
        print("=" * 80)
        print("🔧 Investigating LLM initialization and voice transcription issues")
        
        # Run all tests
        self.test_environment_variables()
        self.test_dependencies()
        self.test_openai_initialization()
        self.test_whisper_initialization()
        self.test_voice_synthesis_initialization()
        self.test_server_websocket_functionality()
        
        # Generate report
        return self.generate_diagnostics_report()

def main():
    diagnostics = DeepDiagnostics()
    return diagnostics.run_all_diagnostics()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 