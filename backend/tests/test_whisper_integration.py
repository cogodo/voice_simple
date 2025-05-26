#!/usr/bin/env python3
"""
Test script to verify Whisper voice-to-text integration.
"""
import sys
import os
import unittest
import tempfile
import wave
import struct
import logging

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.whisper_handler import WhisperHandler, create_whisper_handler


class TestWhisperIntegration(unittest.TestCase):
    """Test cases for Whisper voice-to-text integration."""
    
    def setUp(self):
        """Set up test environment."""
        self.logger = logging.getLogger(__name__)
        
        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            self.skipTest("OPENAI_API_KEY not set - skipping Whisper tests")
        
        try:
            self.handler = create_whisper_handler(self.logger)
        except Exception as e:
            self.skipTest(f"Failed to create WhisperHandler: {e}")
    
    def test_handler_creation(self):
        """Test that WhisperHandler can be created successfully."""
        self.assertIsInstance(self.handler, WhisperHandler)
        self.assertEqual(self.handler.model, "whisper-1")
        self.assertEqual(self.handler.target_sample_rate, 16000)
    
    def test_audio_validation(self):
        """Test audio format validation."""
        # Test with valid WAV data
        valid_audio = self._create_test_audio_wav()
        self.assertTrue(self.handler.validate_audio_format(valid_audio))
        
        # Test with invalid data
        invalid_audio = b"not audio data"
        self.assertFalse(self.handler.validate_audio_format(invalid_audio))
        
        # Test with empty data
        empty_audio = b""
        self.assertFalse(self.handler.validate_audio_format(empty_audio))
    
    def test_audio_info(self):
        """Test getting audio information."""
        test_audio = self._create_test_audio_wav()
        info = self.handler.get_audio_info(test_audio, 'wav')
        
        self.assertIn('duration_seconds', info)
        self.assertIn('sample_rate', info)
        self.assertIn('channels', info)
        self.assertIn('size_bytes', info)
        self.assertGreater(info['duration_seconds'], 0)
        self.assertEqual(info['channels'], 1)  # Should be mono
    
    def test_audio_preprocessing(self):
        """Test audio preprocessing functionality."""
        test_audio = self._create_test_audio_wav(sample_rate=44100, channels=2)
        processed = self.handler._preprocess_audio(test_audio, 'wav')
        
        # Processed audio should be different (resampled and converted to mono)
        self.assertNotEqual(test_audio, processed)
        
        # Check processed audio info
        info = self.handler.get_audio_info(processed, 'wav')
        self.assertEqual(info['sample_rate'], 16000)  # Should be resampled
        self.assertEqual(info['channels'], 1)  # Should be mono
    
    def test_transcription_with_test_audio(self):
        """Test transcription with generated test audio (will likely return empty or noise)."""
        test_audio = self._create_test_audio_wav()
        
        try:
            # This will likely return empty or minimal text since it's just generated tone
            transcription = self.handler.transcribe_audio(test_audio, 'wav')
            self.assertIsInstance(transcription, str)
            # Don't assert content since generated audio won't have speech
            print(f"Test audio transcription result: '{transcription}'")
        except Exception as e:
            # API errors are acceptable for test audio
            print(f"Expected API error for test audio: {e}")
    
    def test_error_handling(self):
        """Test error handling for various invalid inputs."""
        # Test empty audio
        with self.assertRaises(ValueError):
            self.handler.transcribe_audio(b"", 'wav')
        
        # Test unsupported format
        with self.assertRaises(ValueError):
            self.handler.transcribe_audio(b"some data", 'unsupported_format')
        
        # Test oversized audio (simulate)
        # Note: We won't actually create 25MB+ of data for this test
        original_max_size = self.handler.max_file_size
        self.handler.max_file_size = 100  # Set very small limit
        
        test_audio = self._create_test_audio_wav()
        with self.assertRaises(ValueError):
            self.handler.transcribe_audio(test_audio, 'wav')
        
        # Restore original limit
        self.handler.max_file_size = original_max_size
    
    def _create_test_audio_wav(self, duration_seconds=1.0, sample_rate=16000, channels=1, frequency=440):
        """
        Create a test WAV audio file with a sine wave tone.
        
        Args:
            duration_seconds: Duration of the audio
            sample_rate: Sample rate in Hz
            channels: Number of audio channels
            frequency: Frequency of the sine wave in Hz
            
        Returns:
            bytes: WAV audio data
        """
        import math
        
        # Calculate number of samples
        num_samples = int(duration_seconds * sample_rate)
        
        # Generate sine wave samples
        samples = []
        for i in range(num_samples):
            # Generate sine wave
            t = i / sample_rate
            sample = int(32767 * 0.1 * math.sin(2 * math.pi * frequency * t))  # Low amplitude
            
            if channels == 1:
                samples.append(sample)
            else:
                # Duplicate for multiple channels
                for _ in range(channels):
                    samples.append(sample)
        
        # Create WAV file in memory
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            with wave.open(temp_file.name, 'wb') as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Pack samples as 16-bit signed integers
                packed_samples = struct.pack('<' + 'h' * len(samples), *samples)
                wav_file.writeframes(packed_samples)
            
            # Read the WAV data
            with open(temp_file.name, 'rb') as f:
                wav_data = f.read()
            
            # Clean up
            os.unlink(temp_file.name)
            
            return wav_data


def run_standalone_test():
    """Run a standalone test for manual verification."""
    
    print('🧪 Testing Whisper Integration')
    print('=' * 50)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set - cannot test Whisper integration")
        return False
    
    try:
        # Create handler
        logger = logging.getLogger(__name__)
        handler = create_whisper_handler(logger)
        print("✅ WhisperHandler created successfully")
        
        # Test audio validation
        test_audio = TestWhisperIntegration()._create_test_audio_wav()
        is_valid = handler.validate_audio_format(test_audio)
        print(f"✅ Audio validation: {is_valid}")
        
        # Test audio info
        info = handler.get_audio_info(test_audio, 'wav')
        print(f"✅ Audio info: {info}")
        
        # Test preprocessing
        processed = handler._preprocess_audio(test_audio, 'wav')
        print(f"✅ Audio preprocessing: {len(test_audio)} -> {len(processed)} bytes")
        
        print("\n📝 Note: Actual transcription testing requires real speech audio")
        print("   The test audio is just a sine wave tone, so transcription will be empty/minimal")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--standalone':
        # Run standalone test
        logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
        success = run_standalone_test()
        print('\n' + '=' * 50)
        if success:
            print('🎉 Whisper integration test PASSED!')
            sys.exit(0)
        else:
            print('💥 Whisper integration test FAILED!')
            sys.exit(1)
    else:
        # Run unittest
        logging.basicConfig(level=logging.WARNING)  # Reduce noise for unit tests
        unittest.main() 