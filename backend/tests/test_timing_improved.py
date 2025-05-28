#!/usr/bin/env python3
"""
Test script to validate improved audio timing and reduced frame skipping
"""
import socketio
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_improved_timing():
    """Test the improved timing with 20ms pacing."""
    
    print("🎯 Testing Improved Audio Timing")
    print("=" * 50)
    
    sio = socketio.SimpleClient(logger=False, engineio_logger=False)
    
    # Test metrics
    frames_received = 0
    total_bytes = 0
    frame_timestamps = []
    start_time = None
    
    try:
        print("🔌 Connecting to backend...")
        sio.connect('http://localhost:8000', transports=['polling'])
        print("✅ Connected successfully!")
        
        # Simple test text
        test_text = "Testing improved audio timing to reduce frame skipping and underruns."
        
        print(f"📝 Testing with text: '{test_text}'")
        print("📤 Sending start_tts request...")
        
        # Send TTS request
        sio.emit('start_tts', {'text': test_text})
        
        # Monitor frame timing
        timeout_seconds = 20
        start_time = time.time()
        
        print("📡 Monitoring frame timing...")
        
        while time.time() - start_time < timeout_seconds:
            try:
                event = sio.receive(timeout=0.5)
                if event:
                    event_name, data = event
                    
                    if event_name == 'tts_started':
                        print(f"🎵 TTS started: {data}")
                        frame_start_time = time.time()
                    
                    elif event_name == 'pcm_frame':
                        frames_received += 1
                        frame_size = len(data) if isinstance(data, (list, bytes)) else 0
                        total_bytes += frame_size
                        
                        # Record frame timing
                        frame_timestamps.append(time.time())
                        
                        # Progress every 25 frames (0.5 seconds)
                        if frames_received % 25 == 0:
                            elapsed = time.time() - start_time
                            rate = frames_received / elapsed
                            print(f"📦 Frame {frames_received}: Rate={rate:.1f} fps, Size={frame_size}b")
                    
                    elif event_name == 'tts_completed':
                        print(f"🏁 TTS completed: {data}")
                        break
                    
                    elif event_name == 'tts_error':
                        print(f"❌ TTS error: {data}")
                        break
                        
            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"⚠️ Error: {e}")
                continue
        
        # Analyze timing
        total_time = time.time() - start_time
        
        print(f"\n📊 TIMING ANALYSIS:")
        print(f"   • Total frames: {frames_received}")
        print(f"   • Total time: {total_time:.2f}s")
        print(f"   • Average rate: {frames_received/total_time:.1f} fps")
        print(f"   • Target rate: 50 fps")
        
        if len(frame_timestamps) >= 2:
            # Calculate inter-frame intervals
            intervals = []
            for i in range(1, len(frame_timestamps)):
                interval = (frame_timestamps[i] - frame_timestamps[i-1]) * 1000  # ms
                intervals.append(interval)
            
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            print(f"\n⏱️  FRAME INTERVALS:")
            print(f"   • Average: {avg_interval:.1f}ms (target: 20ms)")
            print(f"   • Min: {min_interval:.1f}ms")
            print(f"   • Max: {max_interval:.1f}ms")
            
            # Count intervals that are too fast (potential skips)
            too_fast = sum(1 for i in intervals if i < 15)  # Less than 15ms
            too_slow = sum(1 for i in intervals if i > 30)  # More than 30ms
            
            print(f"   • Too fast (<15ms): {too_fast} ({too_fast/len(intervals)*100:.1f}%)")
            print(f"   • Too slow (>30ms): {too_slow} ({too_slow/len(intervals)*100:.1f}%)")
            
            if avg_interval > 18 and avg_interval < 22:
                print("✅ EXCELLENT: Frame timing is well-controlled!")
            elif avg_interval > 15 and avg_interval < 25:
                print("🟡 GOOD: Frame timing is acceptable")
            else:
                print("🔴 POOR: Frame timing needs improvement")
        
        return frames_received > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        try:
            sio.disconnect()
            print("🔌 Disconnected from backend")
        except:
            pass

if __name__ == "__main__":
    print("🧪 Improved Audio Timing Test")
    print("This test validates 20ms frame pacing and timing control")
    print()
    
    success = test_improved_timing()
    
    if success:
        print("\n✅ Test completed!")
        print("💡 Check the frame intervals - they should be close to 20ms")
        print("   This should reduce frame skipping in Flutter")
    else:
        print("\n❌ Test failed!")
    
    print("\nExpected improvements:")
    print("1. More consistent 20ms frame intervals")
    print("2. Reduced 'too fast' frame delivery") 
    print("3. Better synchronization with Flutter processing") 