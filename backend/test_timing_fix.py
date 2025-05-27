#!/usr/bin/env python3
"""
Test script to verify the audio timing fix eliminates underruns
"""
import socketio
import time
import threading
from collections import defaultdict

def test_timing_fix():
    """Test the timing-controlled TTS streaming."""
    
    print("🎯 Testing Timing-Controlled TTS Streaming")
    print("=" * 50)
    
    # Connect to backend
    sio = socketio.SimpleClient()
    
    try:
        print("🔌 Connecting to backend...")
        sio.connect('http://localhost:8000')
        print("✅ Connected successfully!")
        
        # Test metrics
        metrics = {
            'frames_received': 0,
            'total_bytes': 0,
            'first_frame_time': None,
            'last_frame_time': None,
            'frame_intervals': [],
            'underruns': 0,
            'timing_errors': []
        }
        
        last_frame_time = None
        expected_interval_ms = 20  # 20ms per frame
        tolerance_ms = 5  # Allow 5ms tolerance
        
        def on_tts_started(data):
            print(f"🎵 TTS started: {data}")
            metrics['first_frame_time'] = time.time()
        
        def on_pcm_frame(data):
            nonlocal last_frame_time
            current_time = time.time()
            
            metrics['frames_received'] += 1
            metrics['total_bytes'] += len(data)
            metrics['last_frame_time'] = current_time
            
            # Calculate interval between frames
            if last_frame_time is not None:
                interval_ms = (current_time - last_frame_time) * 1000
                metrics['frame_intervals'].append(interval_ms)
                
                # Check for timing issues
                if interval_ms > (expected_interval_ms + tolerance_ms):
                    metrics['underruns'] += 1
                    if len(metrics['timing_errors']) < 10:  # Log first 10 errors
                        metrics['timing_errors'].append({
                            'frame': metrics['frames_received'],
                            'interval_ms': round(interval_ms, 2),
                            'expected_ms': expected_interval_ms
                        })
            
            last_frame_time = current_time
            
            # Progress indicator
            if metrics['frames_received'] % 50 == 0:
                print(f"📦 Received {metrics['frames_received']} frames...")
        
        def on_tts_completed(data):
            print(f"🏁 TTS completed: {data}")
            
            # Calculate timing metrics
            if metrics['first_frame_time'] and metrics['last_frame_time']:
                total_duration = metrics['last_frame_time'] - metrics['first_frame_time']
                expected_duration = metrics['frames_received'] * expected_interval_ms / 1000
                
                print(f"\n📊 TIMING ANALYSIS:")
                print(f"   • Frames received: {metrics['frames_received']}")
                print(f"   • Total bytes: {metrics['total_bytes']}")
                print(f"   • Actual duration: {total_duration:.3f}s")
                print(f"   • Expected duration: {expected_duration:.3f}s")
                print(f"   • Timing accuracy: {(expected_duration/total_duration*100):.1f}%")
                print(f"   • Underruns detected: {metrics['underruns']}")
                
                if metrics['frame_intervals']:
                    avg_interval = sum(metrics['frame_intervals']) / len(metrics['frame_intervals'])
                    print(f"   • Average frame interval: {avg_interval:.2f}ms (expected: {expected_interval_ms}ms)")
                
                if metrics['timing_errors']:
                    print(f"\n⚠️  TIMING ERRORS (first 10):")
                    for error in metrics['timing_errors']:
                        print(f"      Frame {error['frame']}: {error['interval_ms']}ms (expected: {error['expected_ms']}ms)")
                
                # Assessment
                print(f"\n🎯 ASSESSMENT:")
                if metrics['underruns'] == 0:
                    print("✅ EXCELLENT: No underruns detected! Timing fix successful.")
                elif metrics['underruns'] < 5:
                    print(f"🟡 GOOD: Only {metrics['underruns']} underruns (significant improvement)")
                else:
                    print(f"🔴 NEEDS WORK: {metrics['underruns']} underruns still occurring")
                
                if abs(expected_duration - total_duration) < 0.1:
                    print("✅ EXCELLENT: Timing accuracy within 100ms")
                elif abs(expected_duration - total_duration) < 0.5:
                    print("🟡 GOOD: Timing accuracy within 500ms")
                else:
                    print("🔴 POOR: Timing accuracy off by more than 500ms")
        
        def on_tts_error(data):
            print(f"❌ TTS error: {data}")
        
        # Register event handlers
        sio.on('tts_started', on_tts_started)
        sio.on('pcm_frame', on_pcm_frame)
        sio.on('tts_completed', on_tts_completed)
        sio.on('tts_error', on_tts_error)
        
        # Test with medium-length text
        test_text = "This is a test of the improved audio timing system. The new implementation should deliver audio frames at precisely twenty millisecond intervals, eliminating underruns and providing smooth, continuous audio playback without gaps or overlapping."
        
        print(f"📝 Testing with text: '{test_text[:50]}...'")
        print(f"💡 Expected: {len(test_text.split()) * 3} frames (approx), 20ms intervals, no underruns")
        print()
        
        # Send TTS request
        sio.emit('start_tts', {'text': test_text})
        
        # Wait for completion (timeout after 30 seconds)
        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                event = sio.receive(timeout=1.0)
                if event and event[0] == 'tts_completed':
                    break
            except:
                continue
        
        print("\n" + "=" * 50)
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        try:
            sio.disconnect()
            print("🔌 Disconnected from backend")
        except:
            pass
    
    return True

if __name__ == "__main__":
    print("🧪 Audio Timing Fix Verification Test")
    print("This test verifies that the timing improvements eliminate underruns")
    print()
    
    success = test_timing_fix()
    
    if success:
        print("\n✅ Test completed! Check the timing analysis above.")
    else:
        print("\n❌ Test failed!")
    
    print("\n💡 Compare these results with your previous logs that showed:")
    print("   • 496 underruns in ~8 seconds")
    print("   • Playback ratio of 113.6%")
    print("   • Overlapping audio issues")
    print()
    print("   The new implementation should show:")
    print("   • Zero or minimal underruns")
    print("   • ~100% playback ratio")
    print("   • Consistent 20ms frame intervals") 