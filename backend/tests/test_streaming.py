#!/usr/bin/env python3
"""
Test script for TTS streaming function with real-time audio playback
"""
import sys
import os
import wave
import tempfile
import subprocess
import time
import threading
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.voice_synthesis import my_processing_function_streaming
import logging

# Setup logging with debug level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AudioStreamer:
    def __init__(self, sample_rate=22050):
        self.sample_rate = sample_rate
        self.audio_buffer = bytearray()
        self.is_playing = False
        self.temp_files = []
        
    def add_chunk(self, chunk):
        """Add audio chunk to buffer"""
        self.audio_buffer.extend(chunk)
        
    def save_and_play_complete_audio(self, filename="test_streaming_output.wav"):
        """Save complete audio buffer as WAV and play it"""
        if not self.audio_buffer:
            print("❌ No audio data to save")
            return False
            
        try:
            # Create WAV file
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(self.audio_buffer)
            
            print(f"🎵 Saved complete audio to: {filename}")
            print(f"📊 Audio info: {len(self.audio_buffer)} bytes, {len(self.audio_buffer)/2/self.sample_rate:.2f} seconds")
            
            # Play the audio file
            self.play_audio_file(filename)
            return True
            
        except Exception as e:
            print(f"❌ Error saving/playing audio: {e}")
            return False
    
    def play_audio_file(self, filename):
        """Play audio file using system player"""
        try:
            if sys.platform == "darwin":  # macOS
                print(f"🔊 Playing audio with afplay...")
                subprocess.run(["afplay", filename], check=True)
            elif sys.platform == "linux":  # Linux
                print(f"🔊 Playing audio with aplay...")
                subprocess.run(["aplay", filename], check=True)
            elif sys.platform == "win32":  # Windows
                print(f"🔊 Playing audio with built-in player...")
                os.startfile(filename)
                time.sleep(5)  # Give time for playback
            else:
                print(f"🤷 Unknown platform: {sys.platform}. Audio saved to {filename}")
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error playing audio: {e}")
        except Exception as e:
            print(f"❌ Unexpected error playing audio: {e}")
    
    def create_real_time_chunks(self, chunk_size_seconds=1.0):
        """Create temporary audio files for real-time playback"""
        chunk_size_bytes = int(self.sample_rate * 2 * chunk_size_seconds)  # 2 bytes per sample (int16)
        
        chunk_num = 0
        while len(self.audio_buffer) >= chunk_size_bytes:
            chunk_num += 1
            
            # Extract chunk from buffer
            chunk_data = self.audio_buffer[:chunk_size_bytes]
            self.audio_buffer = self.audio_buffer[chunk_size_bytes:]
            
            # Create temporary file
            temp_file = f"temp_chunk_{chunk_num}.wav"
            
            try:
                with wave.open(temp_file, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(self.sample_rate)
                    wav_file.writeframes(chunk_data)
                
                self.temp_files.append(temp_file)
                
                # Play chunk in background thread
                threading.Thread(target=self._play_chunk_async, args=(temp_file,), daemon=True).start()
                
                print(f"🎵 Playing real-time chunk {chunk_num} ({len(chunk_data)} bytes)")
                
            except Exception as e:
                print(f"❌ Error creating/playing chunk {chunk_num}: {e}")
    
    def _play_chunk_async(self, filename):
        """Play audio chunk asynchronously"""
        try:
            if sys.platform == "darwin":
                subprocess.run(["afplay", filename], check=True)
            # Add delay then cleanup
            time.sleep(0.5)
            try:
                os.remove(filename)
            except:
                pass
        except Exception as e:
            print(f"⚠️ Background playback error: {e}")
    
    def cleanup(self):
        """Clean up temporary files"""
        for temp_file in self.temp_files:
            try:
                os.remove(temp_file)
            except:
                pass

def test_streaming():
    """Test the streaming TTS function with real-time audio playback"""
    chunk_count = 0
    total_bytes = 0
    test_text = 'Hello, this is a test of the streaming audio system. The voice should sound clear and natural without any static or distortion.'
    
    print(f'🎯 Testing TTS streaming with AUDIO PLAYBACK')
    print(f'📝 Text: "{test_text}"')
    print(f'⏱️  Starting streaming test...\n')
    
    # Create audio streamer
    streamer = AudioStreamer()
    
    try:
        start_time = time.time()
        
        print("📡 Receiving audio chunks...")
        for chunk in my_processing_function_streaming(test_text, logger):
            chunk_count += 1
            total_bytes += len(chunk)
            
            # Add chunk to streamer
            streamer.add_chunk(chunk)
            
            # Print progress
            if chunk_count % 10 == 0:
                print(f'📦 Received {chunk_count} chunks ({total_bytes} bytes)...')
            
            # Try real-time playback every few chunks
            if chunk_count % 20 == 0:
                streamer.create_real_time_chunks(0.5)  # 0.5 second chunks
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f'\n✅ TTS Streaming Test complete!')
        print(f'📊 Statistics:')
        print(f'   • Total chunks: {chunk_count}')
        print(f'   • Total bytes: {total_bytes}')
        print(f'   • Streaming time: {duration:.2f} seconds')
        print(f'   • Audio duration: ~{total_bytes/2/22050:.2f} seconds')
        print(f'   • Avg chunk size: {total_bytes/chunk_count if chunk_count > 0 else 0:.0f} bytes')
        
        if chunk_count == 0:
            print("⚠️ Warning: No audio chunks received. This might indicate an API issue.")
            return False
        
        # Play the complete audio
        print(f'\n🎵 Now playing complete audio...')
        success = streamer.save_and_play_complete_audio()
        
        # Cleanup
        streamer.cleanup()
        
        if success:
            print(f'\n🎉 Audio playback test completed successfully!')
            print(f'💡 Listen carefully - the audio should be clear without static!')
        
        return success
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        
        # Cleanup on error
        streamer.cleanup()
        return False

if __name__ == "__main__":
    print("🎤 TTS Streaming Audio Test")
    print("="*50)
    success = test_streaming()
    
    if success:
        print("\n✅ Test completed successfully!")
        print("🔊 If you heard clear audio without static, the fix is working!")
    else:
        print("\n❌ Test failed!")
    
    print("="*50) 