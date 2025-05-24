#!/usr/bin/env python3
"""
Test script for TTS streaming function
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.voice_synthesis import my_processing_function_streaming
import logging

# Setup logging with debug level
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_streaming():
    """Test the streaming TTS function"""
    chunk_count = 0
    total_bytes = 0
    test_text = 'Hello, this is a test'
    
    print(f'Testing TTS streaming with: {test_text}')
    
    try:
        for chunk in my_processing_function_streaming(test_text, logger):
            chunk_count += 1
            total_bytes += len(chunk)
            print(f'Chunk {chunk_count}: {len(chunk)} bytes')
        
        print(f'✅ TTS Streaming Test complete: {chunk_count} chunks, {total_bytes} total bytes')
        
        if chunk_count == 0:
            print("⚠️ Warning: No audio chunks received. This might indicate an API issue.")
        
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_streaming() 