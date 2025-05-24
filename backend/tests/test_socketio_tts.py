#!/usr/bin/env python3
"""
Test Socket.IO TTS streaming functionality
"""
import socketio
import time
import asyncio

def test_socketio_tts():
    """Test TTS via Socket.IO events"""
    sio = socketio.SimpleClient()
    
    print("🔌 Connecting to Socket.IO server...")
    try:
        sio.connect('http://localhost:8000')
        print("✅ Connected successfully!")
        
        # Test the TTS streaming event
        test_text = "Hello! This is a test of the Socket.IO TTS streaming system."
        print(f"🎯 Testing TTS with text: '{test_text}'")
        
        # Listen for audio chunks
        audio_chunks_received = 0
        total_bytes = 0
        
        @sio.event
        def audio_chunk(data):
            nonlocal audio_chunks_received, total_bytes
            if 'audio_chunk' in data:
                audio_chunks_received += 1
                chunk_size = len(data['audio_chunk'])
                total_bytes += chunk_size
                print(f"📦 Audio chunk {audio_chunks_received}: {chunk_size} bytes")
        
        @sio.event
        def tts_starting(data):
            print(f"🎤 TTS starting: {data}")
        
        @sio.event
        def tts_finished(data):
            print(f"🏁 TTS finished: {data}")
        
        @sio.event
        def tts_error(data):
            print(f"❌ TTS error: {data}")
        
        # Send the TTS request
        sio.emit('synthesize_speech_streaming', {'text': test_text})
        
        # Wait for response
        print("⏳ Waiting for TTS response...")
        time.sleep(10)  # Wait 10 seconds for streaming to complete
        
        print(f"📊 Summary: {audio_chunks_received} chunks, {total_bytes} total bytes")
        
        if audio_chunks_received > 0:
            print("✅ TTS streaming test successful!")
        else:
            print("⚠️ No audio chunks received")
        
        sio.disconnect()
        return audio_chunks_received > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_socketio_tts() 