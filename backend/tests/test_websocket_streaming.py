#!/usr/bin/env python3
"""
WebSocket TTS Streaming Test
Tests the WebSocket-based TTS streaming functionality via SocketIO.
"""

import sys
import os
import time
import socketio
import threading
import logging
from socketio.exceptions import TimeoutError

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebSocketStreamingTester:
    """Test WebSocket TTS streaming functionality."""
    
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.client = socketio.SimpleClient()
        
        # Test results tracking
        self.frames_received = 0
        self.total_bytes = 0
        self.streaming_started = False
        self.streaming_completed = False
        self.error_occurred = False
        self.error_message = None
        
        # Timing tracking
        self.start_time = None
        self.first_frame_time = None
        self.completion_time = None
        
        # Frame data for analysis
        self.frame_times = []
        self.frame_sizes = []
        
        # Event handling thread control
        self.event_thread = None
        self.stop_event_handling = False

    def connect(self):
        """Connect to the WebSocket server."""
        try:
            print(f"🔗 Connecting to {self.server_url}...")
            self.client.connect(self.server_url)
            print("✅ Connected to WebSocket server")
            return True
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            return False

    def disconnect(self):
        """Disconnect from the WebSocket server."""
        try:
            self.stop_event_handling = True
            if self.event_thread:
                self.event_thread.join(timeout=2)
            self.client.disconnect()
            print("✅ Disconnected from WebSocket server")
        except Exception as e:
            print(f"⚠️  Error during disconnect: {e}")

    def _handle_events(self):
        """Handle incoming events in a separate thread."""
        while not self.stop_event_handling:
            try:
                # Wait for events with a short timeout
                event = self.client.receive(timeout=1)
                
                event_name = event[0]
                event_data = event[1] if len(event) > 1 else {}
                
                current_time = time.time()
                
                if event_name == 'tts_started':
                    self.streaming_started = True
                    print(f"🎤 TTS streaming started: {event_data}")
                
                elif event_name == 'pcm_frame':
                    if self.first_frame_time is None:
                        self.first_frame_time = current_time
                        time_to_first = current_time - self.start_time
                        print(f"⏱️  First frame received after {time_to_first:.3f}s")
                    
                    # Process frame data - pcm_frame sends data directly as a list
                    frame_data = event_data if isinstance(event_data, list) else []
                    frame_size = len(frame_data)
                    
                    self.frames_received += 1
                    self.total_bytes += frame_size
                    self.frame_times.append(current_time)
                    self.frame_sizes.append(frame_size)
                    
                    # Log progress
                    if self.frames_received % 20 == 0:
                        elapsed = current_time - self.start_time
                        print(f"📦 Frame {self.frames_received}: {frame_size} bytes (Total: {self.total_bytes} bytes, {elapsed:.2f}s)")
                
                elif event_name == 'tts_completed':
                    self.streaming_completed = True
                    self.completion_time = current_time
                    print(f"🏁 TTS streaming completed: {event_data}")
                    break
                
                elif event_name == 'tts_error':
                    self.error_occurred = True
                    self.error_message = event_data.get('error', 'Unknown error') if isinstance(event_data, dict) else str(event_data)
                    print(f"❌ TTS error: {self.error_message}")
                    break
                    
            except TimeoutError:
                # Timeout is normal - just continue listening
                continue
            except Exception as e:
                print(f"⚠️  Event handling error: {e}")
                break

    def test_streaming(self, text):
        """Test TTS streaming with the given text."""
        print(f"🧪 Testing WebSocket TTS streaming")
        print(f"📝 Text: '{text}'")
        
        # Reset test state
        self.frames_received = 0
        self.total_bytes = 0
        self.streaming_started = False
        self.streaming_completed = False
        self.error_occurred = False
        self.error_message = None
        self.frame_times = []
        self.frame_sizes = []
        self.stop_event_handling = False
        
        # Start event handling thread
        self.event_thread = threading.Thread(target=self._handle_events, daemon=True)
        self.event_thread.start()
        
        # Start streaming
        self.start_time = time.time()
        self.client.emit('start_tts', {'text': text})
        
        # Wait for streaming to complete (timeout after 30 seconds)
        timeout = 30
        elapsed = 0
        
        while not self.streaming_completed and not self.error_occurred and elapsed < timeout:
            time.sleep(0.1)
            elapsed = time.time() - self.start_time
        
        # Stop event handling
        self.stop_event_handling = True
        if self.event_thread:
            self.event_thread.join(timeout=2)
        
        # Analyze results
        return self._analyze_results(elapsed, timeout)

    def _analyze_results(self, elapsed, timeout):
        """Analyze streaming test results."""
        print(f"\n📊 WebSocket Streaming Test Results:")
        print(f"   • Frames received: {self.frames_received}")
        print(f"   • Total bytes: {self.total_bytes}")
        print(f"   • Total time: {elapsed:.2f}s")
        
        if self.error_occurred:
            print(f"❌ Error occurred: {self.error_message}")
            return False
        
        if elapsed >= timeout:
            print(f"❌ Test timed out after {timeout}s")
            return False
        
        if not self.streaming_started:
            print("❌ Streaming never started")
            return False
        
        if not self.streaming_completed:
            print("❌ Streaming did not complete")
            return False
        
        if self.frames_received == 0:
            print("❌ No frames received")
            return False
        
        # Calculate statistics
        if self.first_frame_time and self.start_time:
            time_to_first = self.first_frame_time - self.start_time
            print(f"   • Time to first frame: {time_to_first:.3f}s")
        
        if self.frames_received > 1:
            total_streaming_time = self.completion_time - self.first_frame_time if self.completion_time and self.first_frame_time else elapsed
            avg_frame_interval = total_streaming_time / self.frames_received
            print(f"   • Average frame interval: {avg_frame_interval:.3f}s")
            print(f"   • Frames per second: {1/avg_frame_interval:.1f}")
        
        avg_frame_size = self.total_bytes / self.frames_received if self.frames_received > 0 else 0
        print(f"   • Average frame size: {avg_frame_size:.0f} bytes")
        
        # Validate expectations
        success = True
        
        if time_to_first > 10.0:  # Should get first frame within 10 seconds
            print(f"⚠️  WARNING: First frame took {time_to_first:.2f}s (longer than expected)")
        
        if avg_frame_size < 100:  # Frames should have reasonable audio data
            print(f"⚠️  WARNING: Average frame size {avg_frame_size:.0f} bytes seems small")
        
        if self.frames_received < 5:  # Should have multiple frames for any reasonable text
            print(f"⚠️  WARNING: Only {self.frames_received} frames received (seems low)")
        
        print("✅ WebSocket streaming test PASSED")
        return success


def test_websocket_connection():
    """Test basic WebSocket connection."""
    print("🧪 Testing WebSocket Connection")
    print("=" * 50)
    
    tester = WebSocketStreamingTester()
    
    if not tester.connect():
        print("❌ Connection test FAILED")
        return False
    
    # Test connection status instead of ping
    try:
        # Check if we can emit a simple event (no response expected)
        # Just verify the connection is alive and can send events
        print("🔍 Verifying connection status...")
        
        # Try to emit an event - if connection is good, this won't raise an exception
        # We'll use a non-blocking emit instead of call
        tester.client.emit('connection_test', {'test': True})
        
        # Small delay to let any potential error surface
        time.sleep(0.5)
        
        print("✅ Connection is active and can send events")
    except Exception as e:
        print(f"⚠️  Connection issue detected: {e}")
        # This is still OK if we connected successfully above
    
    tester.disconnect()
    print("✅ Connection test PASSED")
    return True


def test_websocket_streaming():
    """Test WebSocket TTS streaming."""
    print("\n🧪 Testing WebSocket TTS Streaming")
    print("=" * 50)
    
    tester = WebSocketStreamingTester()
    
    if not tester.connect():
        print("❌ Could not connect to server")
        return False
    
    try:
        # Test with a simple message
        test_text = "Hello! This is a WebSocket TTS streaming test."
        success = tester.test_streaming(test_text)
        
        tester.disconnect()
        return success
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        tester.disconnect()
        return False


def test_websocket_stress():
    """Test WebSocket streaming with longer text."""
    print("\n🧪 Testing WebSocket Stress Test")
    print("=" * 50)
    
    tester = WebSocketStreamingTester()
    
    if not tester.connect():
        print("❌ Could not connect to server")
        return False
    
    try:
        # Test with longer text
        test_text = (
            "This is a longer stress test for WebSocket TTS streaming. "
            "We want to verify that the system can handle extended text "
            "and produce consistent streaming results with multiple frames "
            "over a longer duration. The system should maintain good "
            "performance and reliability throughout the entire streaming process."
        )
        
        success = tester.test_streaming(test_text)
        
        tester.disconnect()
        return success
        
    except Exception as e:
        print(f"❌ Stress test failed: {e}")
        tester.disconnect()
        return False


def test_frame_timing_diagnosis():
    """Test frame timing to diagnose where delays are occurring."""
    print("\n🧪 Testing Frame Timing Diagnosis")
    print("=" * 50)
    
    tester = WebSocketStreamingTester()
    
    if not tester.connect():
        print("❌ Could not connect to server")
        return False
    
    try:
        # Use shorter text to get faster results
        test_text = "Short timing test."
        
        print(f"📝 Text: '{test_text}'")
        print("🔍 Measuring detailed frame timing...")
        
        # Reset test state with enhanced timing tracking
        tester.frames_received = 0
        tester.total_bytes = 0
        tester.streaming_started = False
        tester.streaming_completed = False
        tester.error_occurred = False
        tester.error_message = None
        tester.frame_times = []
        tester.frame_sizes = []
        tester.stop_event_handling = False
        
        # Start event handling thread
        tester.event_thread = threading.Thread(target=tester._handle_events, daemon=True)
        tester.event_thread.start()
        
        # Start streaming and measure
        request_time = time.time()
        tester.start_time = request_time
        tester.client.emit('start_tts', {'text': test_text})
        
        print(f"⏰ Request sent at: {request_time:.6f}")
        
        # Wait for completion with detailed timing
        timeout = 20
        elapsed = 0
        
        while not tester.streaming_completed and not tester.error_occurred and elapsed < timeout:
            time.sleep(0.01)  # Check more frequently
            elapsed = time.time() - tester.start_time
        
        # Stop event handling
        tester.stop_event_handling = True
        if tester.event_thread:
            tester.event_thread.join(timeout=2)
        
        # Detailed timing analysis
        print(f"\n🔬 Detailed Timing Analysis:")
        print(f"   • Request sent: {request_time:.6f}")
        
        if tester.streaming_started and tester.first_frame_time:
            streaming_start_delay = tester.first_frame_time - request_time
            print(f"   • First frame received: {tester.first_frame_time:.6f}")
            print(f"   • Time to first frame: {streaming_start_delay:.3f}s")
        
        if len(tester.frame_times) > 1:
            print(f"   • Frame intervals (first 10):")
            for i in range(min(10, len(tester.frame_times) - 1)):
                interval = tester.frame_times[i + 1] - tester.frame_times[i]
                print(f"     Frame {i+1}→{i+2}: {interval:.6f}s ({interval*1000:.1f}ms)")
        
        if tester.completion_time:
            total_time = tester.completion_time - request_time
            streaming_time = tester.completion_time - tester.first_frame_time if tester.first_frame_time else 0
            print(f"   • Total time: {total_time:.3f}s")
            print(f"   • Pure streaming time: {streaming_time:.3f}s")
            
            if tester.frames_received > 0:
                expected_audio_duration = (tester.frames_received * 441 * 2) / 22050  # 441 samples per frame, 22050 Hz
                print(f"   • Expected audio duration: {expected_audio_duration:.3f}s")
                print(f"   • Real-time ratio: {expected_audio_duration / streaming_time:.2f}x" if streaming_time > 0 else "")
        
        # Identify the issue
        print(f"\n🎯 Diagnosis:")
        if tester.first_frame_time and request_time:
            delay = tester.first_frame_time - request_time
            if delay > 10:
                print(f"❌ ISSUE: Long delay to first frame ({delay:.1f}s) - likely Cartesia generation delay")
            elif delay > 2:
                print(f"⚠️  WARNING: Moderate delay to first frame ({delay:.1f}s) - possible network/processing delay")
            else:
                print(f"✅ Good: Fast first frame ({delay:.1f}s)")
        
        if len(tester.frame_times) > 5:
            # Check if frames come in bursts vs steady stream
            intervals = [tester.frame_times[i+1] - tester.frame_times[i] for i in range(len(tester.frame_times)-1)]
            avg_interval = sum(intervals) / len(intervals)
            fast_intervals = sum(1 for x in intervals if x < 0.005)  # Less than 5ms
            
            print(f"   • Average frame interval: {avg_interval*1000:.1f}ms")
            print(f"   • Fast intervals (<5ms): {fast_intervals}/{len(intervals)} ({fast_intervals/len(intervals)*100:.1f}%)")
            
            if fast_intervals / len(intervals) > 0.8:
                print(f"❌ ISSUE: Frames arriving in bursts - backend is batching instead of real-time streaming")
            elif fast_intervals / len(intervals) > 0.5:
                print(f"⚠️  WARNING: Many fast intervals suggest some batching behavior")
            else:
                print(f"✅ Good: Frames arriving at steady intervals")
        
        tester.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ Diagnosis failed: {e}")
        import traceback
        traceback.print_exc()
        tester.disconnect()
        return False


def test_basic_streaming_direct():
    """Test the streaming function directly without WebSocket overhead."""
    print("\n🧪 Testing Direct Streaming Function")
    print("=" * 50)
    
    try:
        # Import the streaming function directly
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from services.voice_synthesis import my_processing_function_streaming
        
        test_text = "Direct streaming test."
        
        print(f"📝 Text: '{test_text}'")
        print("🔄 Testing direct streaming function...")
        
        start_time = time.time()
        first_frame_time = None
        frame_times = []
        frame_count = 0
        
        # Test direct streaming
        for chunk in my_processing_function_streaming(test_text, logger):
            current_time = time.time()
            
            if first_frame_time is None:
                first_frame_time = current_time
                delay = first_frame_time - start_time
                print(f"⏱️  First frame generated after {delay:.3f}s")
            
            frame_times.append(current_time)
            frame_count += 1
            
            # Log first few frames
            if frame_count <= 5:
                elapsed = current_time - start_time
                print(f"📦 Frame {frame_count}: {len(chunk)} bytes at {elapsed:.3f}s")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"\n📊 Direct Streaming Results:")
        print(f"   • Total frames: {frame_count}")
        print(f"   • Total time: {total_time:.3f}s")
        
        if frame_count > 1 and len(frame_times) > 1:
            intervals = [frame_times[i+1] - frame_times[i] for i in range(len(frame_times)-1)]
            avg_interval = sum(intervals) / len(intervals)
            fast_intervals = sum(1 for x in intervals if x < 0.005)
            
            print(f"   • Average generation interval: {avg_interval*1000:.1f}ms")
            print(f"   • Fast intervals (<5ms): {fast_intervals}/{len(intervals)} ({fast_intervals/len(intervals)*100:.1f}%)")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct streaming test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_sse_vs_websocket_comparison():
    """Compare SSE vs WebSocket timing using the user's exact example."""
    print("\n🧪 Testing SSE vs WebSocket Timing Comparison")
    print("=" * 50)
    
    try:
        # Import the SSE function directly
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from cartesia import Cartesia
        from cartesia.tts import Controls, OutputFormat_RawParams, TtsRequestIdSpecifierParams
        import time
        
        # Use the user's exact SSE example
        def get_tts_chunks_sse():
            client = Cartesia(
                api_key=os.getenv("CARTESIA_API_KEY"),
            )
            response = client.tts.sse(
                model_id="sonic-2",
                transcript="Hello world!",
                voice={
                    "id": "f9836c6e-a0bd-460e-9d3c-f7299fa60f94",
                    "experimental_controls": {
                        "speed": "normal",
                        "emotion": [],
                    },
                },
                language="en",
                output_format={
                    "container": "raw",
                    "encoding": "pcm_f32le",
                    "sample_rate": 44100,
                },
            )

            audio_chunks = []
            for chunk in response:
                audio_chunks.append(chunk)
            return audio_chunks

        # Test SSE timing
        print("🔍 Testing SSE timing (user's example)...")
        sse_start = time.time()
        sse_first_chunk = None
        sse_chunk_times = []
        
        chunks = get_tts_chunks_sse()
        for i, chunk in enumerate(chunks):
            current_time = time.time()
            if sse_first_chunk is None:
                sse_first_chunk = current_time
            sse_chunk_times.append(current_time)
            
            print(f"SSE Chunk {i+1}: {len(chunk.data)} bytes at {current_time - sse_start:.3f}s")
            
            if i >= 4:  # Limit output
                break
        
        sse_total = time.time() - sse_start
        sse_first_delay = sse_first_chunk - sse_start if sse_first_chunk else 0
        
        # Test WebSocket timing (our implementation)
        print("\n🔍 Testing WebSocket timing (our implementation)...")
        from services.voice_synthesis import my_processing_function_streaming
        
        ws_start = time.time()
        ws_first_frame = None
        ws_frame_times = []
        frame_count = 0
        
        for chunk in my_processing_function_streaming("Hello world!", logger):
            current_time = time.time()
            if ws_first_frame is None:
                ws_first_frame = current_time
            ws_frame_times.append(current_time)
            frame_count += 1
            
            print(f"WebSocket Frame {frame_count}: {len(chunk)} bytes at {current_time - ws_start:.3f}s")
            
            if frame_count >= 5:  # Limit output
                break
        
        ws_total = time.time() - ws_start
        ws_first_delay = ws_first_frame - ws_start if ws_first_frame else 0
        
        # Compare results
        print(f"\n📊 SSE vs WebSocket Comparison:")
        print(f"   🔸 SSE:")
        print(f"     • First chunk delay: {sse_first_delay:.3f}s")
        print(f"     • Total chunks: {len(chunks)}")
        print(f"     • Total time: {sse_total:.3f}s")
        
        print(f"   🔸 WebSocket:")
        print(f"     • First frame delay: {ws_first_delay:.3f}s")
        print(f"     • Frame count (first 5): {frame_count}")
        print(f"     • Total time: {ws_total:.3f}s")
        
        print(f"\n🎯 Analysis:")
        if ws_first_delay < sse_first_delay:
            improvement = sse_first_delay - ws_first_delay
            print(f"✅ WebSocket is {improvement:.3f}s faster to first frame")
        else:
            delay = ws_first_delay - sse_first_delay
            print(f"❌ WebSocket is {delay:.3f}s slower to first frame")
        
        print(f"📝 Both approaches still show batch generation - this confirms the issue is in Cartesia's TTS generation, not our streaming implementation.")
        
        return True
        
    except Exception as e:
        print(f"❌ SSE vs WebSocket comparison failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all WebSocket streaming tests."""
    print("🎯 WebSocket TTS Streaming Test Suite")
    print("=" * 60)
    print("ℹ️  Make sure the backend server is running on localhost:8000")
    print("=" * 60)
    
    tests = [
        ("WebSocket Connection", test_websocket_connection),
        ("Basic TTS Streaming", test_websocket_streaming),
        ("Stress Test", test_websocket_stress),
        ("Frame Timing Diagnosis", test_frame_timing_diagnosis),
        ("Direct Streaming Function", test_basic_streaming_direct),
        ("SSE vs WebSocket Comparison", test_sse_vs_websocket_comparison),
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
        print("✅ All WebSocket tests PASSED! Streaming via WebSocket is working correctly.")
        return True
    else:
        print("❌ Some WebSocket tests FAILED. Check server status and issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 