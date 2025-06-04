"""
Simple test suite for voice integration functionality.
Tests basic voice event handling and WebSocket communication.
"""

import unittest
import base64
import io
import os
import sys
import wave
import numpy as np

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


class TestVoiceIntegrationSimple(unittest.TestCase):
    """Simple test for voice integration functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app, self.socketio = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.socketio_client = self.socketio.test_client(self.app)

        # Create test audio data
        self.test_audio_data = self._create_test_audio()

    def tearDown(self):
        """Clean up after tests."""
        if hasattr(self, "socketio_client"):
            self.socketio_client.disconnect()

    def _create_test_audio(self):
        """Create test audio data (16kHz mono WAV)."""
        # Generate 1 second of sine wave at 440Hz
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)

        # Convert to 16-bit PCM
        audio_data = (audio_data * 32767).astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.getvalue()

    def test_websocket_connection(self):
        """Test basic WebSocket connection."""
        self.assertTrue(self.socketio_client.is_connected())

        # Check that we received conversation_ready event
        received = self.socketio_client.get_received()
        event_names = [event["name"] for event in received]
        self.assertIn("conversation_ready", event_names)

    def test_start_voice_recording_event(self):
        """Test start voice recording event handling."""
        # Clear any existing events
        self.socketio_client.get_received()

        # Emit start_voice_recording event
        self.socketio_client.emit("start_voice_recording", {})

        # Check received events
        received = self.socketio_client.get_received()
        event_names = [event["name"] for event in received]

        # Should receive voice_recording_started event
        self.assertIn("voice_recording_started", event_names)

    def test_voice_chunk_event(self):
        """Test voice chunk event handling."""
        # Clear any existing events
        self.socketio_client.get_received()

        # Start recording first
        self.socketio_client.emit("start_voice_recording", {})

        # Send voice chunk
        audio_base64 = base64.b64encode(self.test_audio_data).decode("utf-8")
        chunk_data = {
            "audio_data": audio_base64,
            "format": "wav",
            "chunk_id": "test_chunk_1",
        }

        self.socketio_client.emit("voice_chunk", chunk_data)

        # Check received events
        received = self.socketio_client.get_received()
        event_names = [event["name"] for event in received]

        # Should receive voice_recording_started and voice_chunk_received events
        self.assertIn("voice_recording_started", event_names)
        self.assertIn("voice_chunk_received", event_names)

    def test_cancel_voice_input_event(self):
        """Test cancel voice input event handling."""
        # Clear any existing events
        self.socketio_client.get_received()

        # Start recording first
        self.socketio_client.emit("start_voice_recording", {})

        # Cancel input
        self.socketio_client.emit("cancel_voice_input", {})

        # Check received events
        received = self.socketio_client.get_received()
        event_names = [event["name"] for event in received]

        # Should receive voice_input_cancelled event
        self.assertIn("voice_input_cancelled", event_names)

    def test_voice_data_event_structure(self):
        """Test voice data event structure without actual transcription."""
        # Clear any existing events
        self.socketio_client.get_received()

        # Send voice data (this will fail transcription but should handle the event)
        audio_base64 = base64.b64encode(self.test_audio_data).decode("utf-8")
        voice_data = {"audio_data": audio_base64, "format": "wav"}

        self.socketio_client.emit("voice_data", voice_data)

        # Check received events
        received = self.socketio_client.get_received()
        event_names = [event["name"] for event in received]

        # Should receive transcription_started event at minimum
        self.assertIn("transcription_started", event_names)

        # May also receive transcription_complete or transcription_error
        # depending on whether OpenAI API is available
        transcription_events = [
            name
            for name in event_names
            if name in ["transcription_complete", "transcription_error"]
        ]
        self.assertTrue(len(transcription_events) > 0)


def run_simple_voice_tests():
    """Run simple voice integration tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestVoiceIntegrationSimple)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Simple Voice Integration Tests...")
    print("=" * 50)

    success = run_simple_voice_tests()

    if success:
        print("\n✅ All simple voice integration tests passed!")
    else:
        print("\n❌ Some simple voice integration tests failed!")
        sys.exit(1)
