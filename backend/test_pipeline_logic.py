#!/usr/bin/env python3
"""
Test the unified TTS pipeline logic without requiring a running server.
Tests that both auto-TTS functions emit the correct events.
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from unittest.mock import Mock, patch
from flask import Flask
from flask_socketio import SocketIO

class PipelineLogicTest:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.logger = Mock()
        self.mock_emit = Mock()
        self.test_results = {}
    
    def test_conversation_auto_tts(self):
        """Test that conversation auto-TTS emits start_tts event."""
        print("🧪 Test 1: Conversation Auto-TTS Logic")
        
        # Import the function
        from websocket.conversation_events import register_conversation_events
        
        # Create a mock socketio object
        mock_socketio = Mock()
        
        # Register the events to get the internal function
        register_conversation_events(mock_socketio, self.app)
        
        # Test the auto-TTS trigger logic directly
        with patch('websocket.conversation_events.emit') as mock_emit:
            # Import the internal function
            try:
                from websocket.conversation_events import _trigger_auto_tts
                
                test_text = "Test conversation auto-TTS"
                _trigger_auto_tts(test_text, self.app)
                
                # Check if start_tts was emitted
                start_tts_calls = [call for call in mock_emit.call_args_list 
                                 if call[0][0] == 'start_tts']
                
                if start_tts_calls:
                    call_data = start_tts_calls[0][0][1]  # Get the data parameter
                    text_matches = call_data.get('text') == test_text
                    
                    print(f"   📊 start_tts emitted: ✅")
                    print(f"   📊 Text matches: {'✅' if text_matches else '❌'}")
                    print(f"   📊 Call data: {call_data}")
                    
                    success = text_matches
                else:
                    print(f"   📊 start_tts emitted: ❌")
                    print(f"   📊 All calls: {[call[0][0] for call in mock_emit.call_args_list]}")
                    success = False
                
            except ImportError as e:
                print(f"   ❌ Could not import _trigger_auto_tts: {e}")
                success = False
        
        self.test_results['conversation_auto_tts'] = success
        
        if success:
            print("   ✅ Conversation Auto-TTS test PASSED")
        else:
            print("   ❌ Conversation Auto-TTS test FAILED")
        
        return success
    
    def test_voice_auto_tts(self):
        """Test that voice auto-TTS emits start_tts event."""
        print("\n🧪 Test 2: Voice Auto-TTS Logic")
        
        with patch('websocket.voice_events.emit') as mock_emit:
            try:
                from websocket.voice_events import _trigger_auto_tts
                
                test_text = "Test voice auto-TTS"
                _trigger_auto_tts(test_text, self.app)
                
                # Check if start_tts was emitted
                start_tts_calls = [call for call in mock_emit.call_args_list 
                                 if call[0][0] == 'start_tts']
                
                if start_tts_calls:
                    call_data = start_tts_calls[0][0][1]  # Get the data parameter
                    text_matches = call_data.get('text') == test_text
                    
                    print(f"   📊 start_tts emitted: ✅")
                    print(f"   📊 Text matches: {'✅' if text_matches else '❌'}")
                    print(f"   📊 Call data: {call_data}")
                    
                    success = text_matches
                else:
                    print(f"   📊 start_tts emitted: ❌")
                    print(f"   📊 All calls: {[call[0][0] for call in mock_emit.call_args_list]}")
                    success = False
                
            except ImportError as e:
                print(f"   ❌ Could not import _trigger_auto_tts: {e}")
                success = False
        
        self.test_results['voice_auto_tts'] = success
        
        if success:
            print("   ✅ Voice Auto-TTS test PASSED")
        else:
            print("   ❌ Voice Auto-TTS test FAILED")
        
        return success
    
    def test_tts_event_handlers(self):
        """Test that TTS event handlers are properly registered."""
        print("\n🧪 Test 3: TTS Event Handlers")
        
        try:
            from websocket.tts_events import register_tts_events
            
            mock_socketio = Mock()
            register_tts_events(mock_socketio, self.app)
            
            # Check that socketio.on was called for the expected events
            expected_events = ['start_tts', 'synthesize_speech_streaming', 'stop_tts']
            registered_events = []
            
            for call in mock_socketio.on.call_args_list:
                event_name = call[0][0]  # First argument to .on() is the event name
                registered_events.append(event_name)
            
            print(f"   📊 Registered events: {registered_events}")
            
            missing_events = [event for event in expected_events if event not in registered_events]
            extra_events = [event for event in registered_events if event not in expected_events]
            
            if not missing_events:
                print(f"   📊 All expected events registered: ✅")
                success = True
            else:
                print(f"   📊 Missing events: {missing_events} ❌")
                success = False
            
            if extra_events:
                print(f"   📊 Additional events: {extra_events}")
            
        except Exception as e:
            print(f"   ❌ Error testing TTS event handlers: {e}")
            success = False
        
        self.test_results['tts_event_handlers'] = success
        
        if success:
            print("   ✅ TTS Event Handlers test PASSED")
        else:
            print("   ❌ TTS Event Handlers test FAILED")
        
        return success
    
    def verify_unified_pipeline(self):
        """Verify that the pipeline logic is unified."""
        print("\n🔍 Verifying Unified Pipeline Logic...")
        
        all_tests_passed = all(self.test_results.values())
        
        if all_tests_passed:
            print("✅ ALL LOGIC TESTS PASSED - Unified pipeline logic verified!")
            print("🎉 Both conversation and voice auto-TTS use start_tts event")
            print("📋 All expected event handlers are registered")
            return True
        else:
            print("❌ Some logic tests failed:")
            for test_name, result in self.test_results.items():
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"   {test_name}: {status}")
            return False
    
    def run_all_tests(self):
        """Run all logic tests."""
        print("🧪 UNIFIED TTS PIPELINE LOGIC TEST SUITE")
        print("=" * 60)
        print("📝 Testing pipeline logic without requiring running server")
        
        # Run tests
        test1 = self.test_conversation_auto_tts()
        test2 = self.test_voice_auto_tts()
        test3 = self.test_tts_event_handlers()
        
        # Verify unified pipeline
        unified_success = self.verify_unified_pipeline()
        
        print("\n" + "=" * 60)
        print("🎯 LOGIC TEST RESULTS:")
        print("=" * 60)
        
        if unified_success:
            print("🎉 SUCCESS: Unified TTS pipeline logic is correct!")
            print("✅ Auto-TTS functions emit the same start_tts event")
            print("🔧 Event handlers are properly registered")
            print("\n📌 Next step: Test with running server to verify full flow")
        else:
            print("⚠️ LOGIC ISSUES DETECTED: Pipeline needs fixes")
            print("📋 Check the specific test results above")
        
        return unified_success

def main():
    tester = PipelineLogicTest()
    return tester.run_all_tests()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 