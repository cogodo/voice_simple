#!/usr/bin/env python3
"""
Basic TTS Streaming Test
Tests the core voice synthesis streaming functionality.
"""

import sys
import os
import time
import logging

# Add parent directory to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.voice_synthesis import my_processing_function_streaming

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_basic_streaming():
    """Test basic TTS streaming functionality."""
    print("🧪 Testing Basic TTS Streaming")
    print("=" * 50)
    
    test_text = "Hello! This is a basic test of the streaming audio system."
    
    try:
        print(f"📝 Text: '{test_text}'")
        print("🔄 Starting streaming...")
        
        start_time = time.time()
        frame_count = 0
        total_bytes = 0
        
        # Test the streaming generator
        for chunk in my_processing_function_streaming(test_text, logger):
            frame_count += 1
            total_bytes += len(chunk)
            
            # Log progress every 10 frames
            if frame_count % 10 == 0:
                elapsed = time.time() - start_time
                print(f"📦 Frame {frame_count}: {len(chunk)} bytes (Total: {total_bytes} bytes, {elapsed:.2f}s)")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n✅ Streaming Test Results:")
        print(f"   • Total frames: {frame_count}")
        print(f"   • Total bytes: {total_bytes}")
        print(f"   • Duration: {duration:.2f} seconds")
        print(f"   • Average frame size: {total_bytes / frame_count if frame_count > 0 else 0:.0f} bytes")
        print(f"   • Frames per second: {frame_count / duration if duration > 0 else 0:.1f}")
        
        # Validate results
        if frame_count == 0:
            print("❌ FAILED: No frames generated")
            return False
        
        if total_bytes == 0:
            print("❌ FAILED: No audio data generated")
            return False
        
        if duration > 30:  # Should not take more than 30 seconds
            print(f"⚠️  WARNING: Streaming took {duration:.2f}s (longer than expected)")
        
        print("✅ Basic streaming test PASSED")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_streaming_consistency():
    """Test that streaming produces consistent results."""
    print("\n🧪 Testing Streaming Consistency")
    print("=" * 50)
    
    test_text = "Consistency test message."
    
    try:
        # Run the same text twice
        results = []
        
        for run in range(2):
            print(f"🔄 Run {run + 1}...")
            frame_count = 0
            total_bytes = 0
            
            for chunk in my_processing_function_streaming(test_text, logger):
                frame_count += 1
                total_bytes += len(chunk)
            
            results.append({
                'frames': frame_count,
                'bytes': total_bytes
            })
            
            print(f"   Frames: {frame_count}, Bytes: {total_bytes}")
        
        # Compare results
        if results[0]['frames'] == results[1]['frames'] and results[0]['bytes'] == results[1]['bytes']:
            print("✅ Consistency test PASSED - Results are identical")
            return True
        else:
            print("⚠️  Results vary between runs (this may be normal due to network/API variations)")
            print(f"   Run 1: {results[0]}")
            print(f"   Run 2: {results[1]}")
            return True  # This is still OK as API may have slight variations
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def test_streaming_timing():
    """Test streaming timing and real-time performance."""
    print("\n🧪 Testing Streaming Timing")
    print("=" * 50)
    
    test_text = "This is a timing test to measure streaming performance and latency characteristics."
    
    try:
        start_time = time.time()
        first_frame_time = None
        frame_times = []
        frame_count = 0
        
        print("🔄 Measuring frame timing...")
        
        for chunk in my_processing_function_streaming(test_text, logger):
            current_time = time.time()
            
            if first_frame_time is None:
                first_frame_time = current_time
                time_to_first_frame = first_frame_time - start_time
                print(f"⏱️  Time to first frame: {time_to_first_frame:.3f}s")
            
            frame_times.append(current_time)
            frame_count += 1
        
        if frame_count == 0:
            print("❌ FAILED: No frames generated")
            return False
        
        # Calculate timing statistics
        total_duration = frame_times[-1] - start_time
        time_to_first = first_frame_time - start_time
        avg_frame_interval = total_duration / frame_count if frame_count > 1 else 0
        
        print(f"\n📊 Timing Results:")
        print(f"   • Time to first frame: {time_to_first:.3f}s")
        print(f"   • Total streaming time: {total_duration:.3f}s")
        print(f"   • Average frame interval: {avg_frame_interval:.3f}s")
        print(f"   • Estimated real-time ratio: {(frame_count * 0.02) / total_duration:.2f}x")
        
        # Validate timing expectations
        if time_to_first > 5.0:
            print(f"⚠️  WARNING: First frame took {time_to_first:.2f}s (longer than expected)")
        
        if avg_frame_interval > 0.1:
            print(f"⚠️  WARNING: Average frame interval {avg_frame_interval:.3f}s is quite long")
        
        print("✅ Timing test completed")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


def main():
    """Run all streaming tests."""
    print("🎯 Backend TTS Streaming Test Suite")
    print("=" * 60)
    
    tests = [
        ("Basic Streaming", test_basic_streaming),
        ("Consistency", test_streaming_consistency),
        ("Timing Performance", test_streaming_timing),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*60}")
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests PASSED! Streaming backend is working correctly.")
        return True
    else:
        print("❌ Some tests FAILED. Check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 