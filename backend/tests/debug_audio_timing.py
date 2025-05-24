#!/usr/bin/env python3
"""
Audio timing debug script to identify bottlenecks in the audio streaming pipeline.
Instruments each stage: capture, send, receive, decode, playback timing.
"""

import socketio
import time
import json
import sys
from datetime import datetime

class AudioTimingDebugger:
    def __init__(self):
        self.events_log = []
        self.chunk_timing = {}
        self.start_time = time.time()
    
    def log_event(self, event_type, chunk_id=None, data_size=None, extra_info=None):
        timestamp = time.time()
        relative_time = timestamp - self.start_time
        
        event = {
            'timestamp': timestamp,
            'relative_time_ms': round(relative_time * 1000, 2),
            'event_type': event_type,
            'chunk_id': chunk_id,
            'data_size': data_size,
            'extra_info': extra_info
        }
        
        self.events_log.append(event)
        
        # Log to console with timing
        timing_str = f"[{relative_time:.3f}s]"
        if chunk_id:
            print(f"{timing_str} {event_type} - Chunk {chunk_id} ({data_size} bytes)")
        else:
            print(f"{timing_str} {event_type}")
    
    def analyze_timing(self):
        print("\n" + "="*80)
        print("🔍 AUDIO TIMING ANALYSIS")
        print("="*80)
        
        # Group events by type
        event_types = {}
        for event in self.events_log:
            event_type = event['event_type']
            if event_type not in event_types:
                event_types[event_type] = []
            event_types[event_type].append(event)
        
        # Analyze chunk timing
        audio_chunks = [e for e in self.events_log if e['event_type'] == 'audio_chunk_received']
        
        if len(audio_chunks) > 1:
            print(f"\n📊 CHUNK TIMING ANALYSIS ({len(audio_chunks)} chunks)")
            print("-" * 50)
            
            intervals = []
            for i in range(1, len(audio_chunks)):
                interval = audio_chunks[i]['relative_time_ms'] - audio_chunks[i-1]['relative_time_ms']
                intervals.append(interval)
                print(f"Chunk {i}: {interval:.1f}ms gap")
            
            avg_interval = sum(intervals) / len(intervals)
            min_interval = min(intervals)
            max_interval = max(intervals)
            
            print(f"\n📈 INTERVAL STATISTICS:")
            print(f"  Average: {avg_interval:.1f}ms")
            print(f"  Min: {min_interval:.1f}ms") 
            print(f"  Max: {max_interval:.1f}ms")
            print(f"  Variation: {max_interval - min_interval:.1f}ms")
            
            # Identify problematic gaps
            problematic = [i for i in intervals if i > 100]  # >100ms gaps
            if problematic:
                print(f"  ⚠️ Problematic gaps (>100ms): {len(problematic)}")
        
        # Analyze data sizes
        chunk_sizes = [e['data_size'] for e in audio_chunks if e['data_size']]
        if chunk_sizes:
            print(f"\n📦 CHUNK SIZE ANALYSIS:")
            print(f"  Average size: {sum(chunk_sizes) / len(chunk_sizes):.0f} bytes")
            print(f"  Min size: {min(chunk_sizes)} bytes")
            print(f"  Max size: {max(chunk_sizes)} bytes")
            print(f"  Total data: {sum(chunk_sizes)} bytes")
        
        return {
            'total_chunks': len(audio_chunks),
            'avg_interval': avg_interval if len(audio_chunks) > 1 else 0,
            'chunk_size_avg': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
            'problematic_gaps': len(problematic) if len(audio_chunks) > 1 else 0
        }

def test_audio_timing():
    """Test audio streaming with detailed timing analysis."""
    
    debugger = AudioTimingDebugger()
    
    print("🎵 Testing Audio Streaming Timing")
    print("=" * 60)
    
    sio = socketio.SimpleClient()
    
    try:
        # Connect
        debugger.log_event("websocket_connect_start")
        sio.connect('http://localhost:8000')
        debugger.log_event("websocket_connected")
        
        time.sleep(0.1)
        
        chunk_count = 0
        
        def track_audio_timing():
            nonlocal chunk_count
            try:
                while True:
                    receive_start = time.time()
                    events = sio.receive(timeout=0.5)
                    
                    if events:
                        receive_time = (time.time() - receive_start) * 1000
                        event_name, data = events[0], events[1]
                        
                        if event_name == 'tts_starting':
                            debugger.log_event("tts_synthesis_started", 
                                             extra_info=data.get('text', '')[:30])
                        
                        elif event_name == 'audio_chunk':
                            chunk_count += 1
                            audio_data = data.get('audio_chunk', [])
                            chunk_data_b64 = data.get('chunk_data', '')
                            
                            debugger.log_event("audio_chunk_received",
                                             chunk_id=chunk_count,
                                             data_size=len(audio_data),
                                             extra_info={
                                                 'receive_time_ms': round(receive_time, 2),
                                                 'base64_size': len(chunk_data_b64),
                                                 'chunk_number': data.get('chunk_number')
                                             })
                        
                        elif event_name == 'tts_finished':
                            debugger.log_event("tts_synthesis_completed",
                                             extra_info=f"Total chunks: {data.get('total_chunks', 0)}")
                            break
                        
                        elif event_name == 'tts_error':
                            debugger.log_event("tts_error", 
                                             extra_info=data.get('error'))
                            break
                    
            except Exception as e:
                if "timeout" not in str(e).lower():
                    debugger.log_event("receive_error", extra_info=str(e))
        
        # Test different text lengths to see chunk behavior
        test_texts = [
            "Short test",
            "Medium length test that should generate several audio chunks",
            "This is a longer test message that will generate many more audio chunks to help us analyze the streaming behavior and identify any timing issues or bottlenecks in the audio pipeline"
        ]
        
        for i, text in enumerate(test_texts):
            print(f"\n🧪 Test {i+1}: '{text[:50]}{'...' if len(text) > 50 else ''}'")
            print("-" * 60)
            
            debugger.log_event("tts_request_sent", extra_info=f"Text length: {len(text)}")
            
            # Send TTS request
            send_start = time.time()
            sio.emit('synthesize_speech_streaming', {'text': text})
            send_time = (time.time() - send_start) * 1000
            
            debugger.log_event("tts_request_transmitted", 
                             extra_info=f"Send time: {send_time:.2f}ms")
            
            # Track this test
            chunk_count = 0
            track_audio_timing()
            
            # Brief pause between tests
            time.sleep(1)
        
        sio.disconnect()
        debugger.log_event("websocket_disconnected")
        
        # Analyze results
        analysis = debugger.analyze_timing()
        
        # Provide recommendations
        print("\n🎯 RECOMMENDATIONS:")
        print("-" * 50)
        
        if analysis['avg_interval'] > 100:
            print("❌ High average interval between chunks (>100ms)")
            print("   → Consider reducing chunk size or implementing jitter buffer")
        
        if analysis['problematic_gaps'] > 0:
            print(f"❌ {analysis['problematic_gaps']} problematic gaps detected")
            print("   → Network latency or backend processing delays")
        
        if analysis['chunk_size_avg'] > 4096:
            print("⚠️ Large chunk sizes detected")
            print("   → Consider smaller chunks for lower latency")
        elif analysis['chunk_size_avg'] < 1024:
            print("⚠️ Very small chunk sizes detected")
            print("   → Consider larger chunks to reduce overhead")
        
        if analysis['total_chunks'] > 0:
            total_time = debugger.events_log[-1]['relative_time_ms']
            throughput = (analysis['chunk_size_avg'] * analysis['total_chunks']) / (total_time / 1000)
            print(f"📊 Data throughput: {throughput:.0f} bytes/sec")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_audio_timing()
    sys.exit(0 if success else 1) 