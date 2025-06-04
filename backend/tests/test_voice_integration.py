"""
Test suite for voice integration functionality.
Tests the complete voice-to-text pipeline including WebSocket events,
Whisper transcription, and conversation integration.
"""

import unittest
import base64
import io
import os
import sys
from unittest.mock import Mock, patch
import wave
import numpy as np

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app
from services.whisper_handler import create_whisper_handler
from websocket.voice_events import register_voice_events


class TestVoiceIntegration(unittest.TestCase):
    """Test voice integration functionality."""

    def setUp(self):
        """Set up test environment."""
        self.app, self.socketio = create_app()
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()
        self.socketio_client = self.socketio.test_client(self.app)

        # Mock voice sessions
        self.voice_sessions = {}

        # Register voice events
        register_voice_events(self.socketio, self.app, self.voice_sessions)

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

    def test_start_voice_recording(self):
        """Test starting voice recording."""
        # Emit start_voice_recording event
        response = self.socketio_client.emit("start_voice_recording", {})

        # Check that the event was handled
        received = self.socketio_client.get_received()

        # Should receive voice_recording_started event
        self.assertTrue(
            any(event["name"] == "voice_recording_started" for event in received)
        )

        # Check that session was created
        session_id = self.socketio_client.sid
        self.assertIn(session_id, self.voice_sessions)

    def test_voice_chunk_processing(self):
        """Test processing voice chunks."""
        # Start recording first
        self.socketio_client.emit("start_voice_recording", {})

        # Send voice chunk
        audio_base64 = base64.b64encode(self.test_audio_data).decode("utf-8")
        chunk_data = {
            "audio_data": audio_base64,
            "format": "wav",
            "chunk_id": "test_chunk_1",
        }

        response = self.socketio_client.emit("voice_chunk", chunk_data)

        # Check that chunk was received
        received = self.socketio_client.get_received()

        # Should receive voice_chunk_received event
        self.assertTrue(
            any(event["name"] == "voice_chunk_received" for event in received)
        )

    @patch("services.whisper_handler.WhisperHandler.transcribe_audio")
    def test_voice_data_transcription(self, mock_transcribe):
        """Test complete voice data transcription."""
        # Mock successful transcription
        mock_transcribe.return_value = "Hello, this is a test transcription."

        # Send complete voice data
        audio_base64 = base64.b64encode(self.test_audio_data).decode("utf-8")
        voice_data = {"audio_data": audio_base64, "format": "wav"}

        response = self.socketio_client.emit("voice_data", voice_data)

        # Check received events
        received = self.socketio_client.get_received()

        # Should receive transcription_started and transcription_complete events
        event_names = [event["name"] for event in received]
        self.assertIn("transcription_started", event_names)
        self.assertIn("transcription_complete", event_names)

        # Check transcription result
        transcription_event = next(
            event for event in received if event["name"] == "transcription_complete"
        )
        self.assertEqual(
            transcription_event["args"][0]["text"],
            "Hello, this is a test transcription.",
        )

    @patch("services.whisper_handler.WhisperHandler.transcribe_audio")
    def test_transcription_error_handling(self, mock_transcribe):
        """Test transcription error handling."""
        # Mock transcription error
        mock_transcribe.side_effect = Exception("Transcription failed")

        # Send voice data
        audio_base64 = base64.b64encode(self.test_audio_data).decode("utf-8")
        voice_data = {"audio_data": audio_base64, "format": "wav"}

        response = self.socketio_client.emit("voice_data", voice_data)

        # Check received events
        received = self.socketio_client.get_received()

        # Should receive transcription_error event
        event_names = [event["name"] for event in received]
        self.assertIn("transcription_error", event_names)

        # Check error message
        error_event = next(
            event for event in received if event["name"] == "transcription_error"
        )
        self.assertIn("error", error_event["args"][0])

    def test_stop_voice_recording(self):
        """Test stopping voice recording."""
        # Start recording first
        self.socketio_client.emit("start_voice_recording", {})

        # Stop recording
        response = self.socketio_client.emit("stop_voice_recording", {})

        # Check received events
        received = self.socketio_client.get_received()

        # Should receive appropriate events
        event_names = [event["name"] for event in received]
        # Note: Actual events depend on implementation
        self.assertTrue(len(received) > 0)

    def test_cancel_voice_input(self):
        """Test cancelling voice input."""
        # Start recording first
        self.socketio_client.emit("start_voice_recording", {})

        # Cancel input
        response = self.socketio_client.emit("cancel_voice_input", {})

        # Check received events
        received = self.socketio_client.get_received()

        # Should receive voice_input_cancelled event
        event_names = [event["name"] for event in received]
        self.assertIn("voice_input_cancelled", event_names)

    @patch("services.whisper_handler.WhisperHandler.transcribe_audio")
    def test_conversation_integration(self, mock_transcribe):
        """Test integration with conversation system."""
        # Mock successful transcription
        mock_transcribe.return_value = "What is the weather like today?"

        # Send voice data
        audio_base64 = base64.b64encode(self.test_audio_data).decode("utf-8")
        voice_data = {"audio_data": audio_base64, "format": "wav"}

        response = self.socketio_client.emit("voice_data", voice_data)

        # Check received events
        received = self.socketio_client.get_received()

        # Should receive user_message event (processed as conversation)
        event_names = [event["name"] for event in received]
        self.assertIn("user_message", event_names)

        # Check that the transcribed text was sent as a user message
        user_message_event = next(
            event for event in received if event["name"] == "user_message"
        )
        self.assertEqual(
            user_message_event["args"][0]["message"], "What is the weather like today?"
        )


class TestWhisperHandler(unittest.TestCase):
    """Test WhisperHandler functionality."""

    def setUp(self):
        """Set up test environment."""
        self.handler = create_whisper_handler()
        self.test_audio_data = self._create_test_audio()

    def _create_test_audio(self):
        """Create test audio data."""
        # Generate simple audio data
        sample_rate = 16000
        duration = 1.0
        frequency = 440.0

        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767).astype(np.int16)

        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data.tobytes())

        wav_buffer.seek(0)
        return wav_buffer.getvalue()

    def test_audio_preprocessing(self):
        """Test audio preprocessing functionality."""
        # Test with valid audio data
        processed_audio = self.handler._preprocess_audio(self.test_audio_data)
        self.assertIsNotNone(processed_audio)
        self.assertIsInstance(processed_audio, bytes)

    def test_audio_validation(self):
        """Test audio validation."""
        # Test with valid audio
        self.assertTrue(self.handler._validate_audio_data(self.test_audio_data))

        # Test with invalid audio
        self.assertFalse(self.handler._validate_audio_data(b"invalid_audio_data"))

        # Test with empty audio
        self.assertFalse(self.handler._validate_audio_data(b""))

    @patch("openai.Audio.transcribe")
    def test_transcription_success(self, mock_transcribe):
        """Test successful transcription."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.text = "This is a test transcription."
        mock_transcribe.return_value = mock_response

        # Test transcription
        result = self.handler.transcribe_audio(self.test_audio_data)
        self.assertEqual(result, "This is a test transcription.")

    @patch("openai.Audio.transcribe")
    def test_transcription_error(self, mock_transcribe):
        """Test transcription error handling."""
        # Mock OpenAI error
        mock_transcribe.side_effect = Exception("API Error")

        # Test transcription
        with self.assertRaises(Exception):
            self.handler.transcribe_audio(self.test_audio_data)

    def test_format_conversion(self):
        """Test audio format conversion."""
        # Test WAV format (should pass through)
        converted = self.handler._convert_to_wav(self.test_audio_data, "wav")
        self.assertEqual(converted, self.test_audio_data)

        # Test unsupported format
        with self.assertRaises(ValueError):
            self.handler._convert_to_wav(b"test_data", "unsupported")


def run_voice_integration_tests():
    """Run all voice integration tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestVoiceIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestWhisperHandler))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    print("Running Voice Integration Tests...")
    print("=" * 50)

    success = run_voice_integration_tests()

    if success:
        print("\n✅ All voice integration tests passed!")
    else:
        print("\n❌ Some voice integration tests failed!")
        sys.exit(1)
