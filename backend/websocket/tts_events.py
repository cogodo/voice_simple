"""
TTS WebSocket event handlers for streaming text-to-speech.
"""
import asyncio
import logging
import struct
import time
from flask_socketio import emit
from flask import request
from services.voice_synthesis import my_processing_function_streaming

def register_tts_events(socketio, app):
    """Register TTS-related WebSocket events."""
    
    # Audio configuration for raw PCM streaming
    SAMPLE_RATE = 22050  # Match Cartesia output
    CHANNELS = 1
    FRAME_SIZE = int(0.02 * SAMPLE_RATE)  # 20ms frames = 441 samples
    FRAME_DURATION_MS = 20  # Each frame represents 20ms of audio
    
    # Session state tracking for concurrent stream management
    active_streams = {}
    
    @socketio.on('start_tts')
    def handle_start_tts(data):
        """Handle TTS streaming request with raw PCM data."""
        try:
            text = data.get('text', '')
            if not text:
                emit('tts_error', {'error': 'No text provided'})
                return
            
            # Get the current session ID
            session_id = request.sid
            app.logger.info(f"Starting TTS streaming for session {session_id}, text: '{text[:50]}...'")
            
            # Stop any existing stream for this session
            if session_id in active_streams:
                active_streams[session_id]['should_stop'] = True
                app.logger.info(f"Stopping previous stream for session {session_id}")
            
            # Initialize new stream state
            active_streams[session_id] = {
                'should_stop': False,
                'start_time': None,
                'frames_sent': 0
            }
            
            # Start streaming task with session ID and timing control
            socketio.start_background_task(stream_tts_pcm_timed, text, session_id, socketio, app, active_streams)
            
        except Exception as e:
            app.logger.error(f"Error starting TTS: {e}")
            emit('tts_error', {'error': str(e)})

    def stream_tts_pcm_timed(text, session_id, socketio_instance, app_instance, stream_tracker):
        """Stream TTS audio as raw PCM frames with proper timing."""
        try:
            app_instance.logger.info(f"Starting PCM-based TTS streaming with timing control for session {session_id}")
            
            # Signal start of streaming to specific client
            socketio_instance.emit('tts_started', {'status': 'streaming'}, room=session_id)
            
            stream_state = stream_tracker[session_id]
            stream_state['start_time'] = time.time()
            
            # Pre-collect all frames to enable proper timing
            app_instance.logger.info("Pre-collecting audio frames for timing control...")
            audio_frames = []
            
            try:
                for frame_data in my_processing_function_streaming(text, app_instance.logger):
                    if stream_state['should_stop']:
                        app_instance.logger.info(f"Stream stopped during collection for session {session_id}")
                        return
                    audio_frames.append(frame_data)
                
                app_instance.logger.info(f"Collected {len(audio_frames)} frames for timed streaming")
                
            except Exception as e:
                app_instance.logger.error(f"Error collecting frames: {e}")
                socketio_instance.emit('tts_error', {'error': f'Frame collection failed: {str(e)}'}, room=session_id)
                return
            
            if not audio_frames:
                app_instance.logger.warning("No audio frames collected")
                socketio_instance.emit('tts_error', {'error': 'No audio generated'}, room=session_id)
                return
            
            # Stream frames with real-time timing
            app_instance.logger.info(f"Starting real-time frame streaming: {len(audio_frames)} frames at {FRAME_DURATION_MS}ms intervals")
            
            for frame_index, frame_data in enumerate(audio_frames):
                # Check if stream should stop
                if stream_state['should_stop']:
                    app_instance.logger.info(f"Stream stopped at frame {frame_index} for session {session_id}")
                    break
                
                # Calculate when this frame should be sent
                expected_time = stream_state['start_time'] + (frame_index * FRAME_DURATION_MS / 1000.0)
                current_time = time.time()
                
                # Wait if we're ahead of schedule
                if current_time < expected_time:
                    sleep_time = expected_time - current_time
                    time.sleep(sleep_time)
                
                # Send frame to specific client
                socketio_instance.emit('pcm_frame', list(frame_data), room=session_id)
                stream_state['frames_sent'] = frame_index + 1
                
                # Log progress occasionally (every 1 second = 50 frames)
                if (frame_index + 1) % 50 == 0:
                    elapsed_time = time.time() - stream_state['start_time']
                    expected_elapsed = (frame_index + 1) * FRAME_DURATION_MS / 1000.0
                    timing_drift = elapsed_time - expected_elapsed
                    app_instance.logger.debug(
                        f"Session {session_id}: Sent {frame_index + 1} frames, "
                        f"elapsed: {elapsed_time:.2f}s, drift: {timing_drift:.3f}s"
                    )
            
            # Stream completed successfully
            frames_sent = stream_state['frames_sent']
            total_duration_ms = frames_sent * FRAME_DURATION_MS
            actual_duration = time.time() - stream_state['start_time']
            
            # Signal completion to specific client
            socketio_instance.emit('tts_completed', {
                'status': 'completed',
                'frames_sent': frames_sent,
                'duration_ms': total_duration_ms,
                'actual_duration_ms': int(actual_duration * 1000),
                'timing_accuracy': f"{((total_duration_ms/1000) / actual_duration * 100):.1f}%"
            }, room=session_id)
            
            app_instance.logger.info(
                f"TTS streaming completed for session {session_id}: "
                f"{frames_sent} frames, {total_duration_ms}ms duration, "
                f"{actual_duration:.2f}s actual time"
            )
            
        except Exception as e:
            app_instance.logger.error(f"Error in TTS streaming for session {session_id}: {e}", exc_info=True)
            # Send error to specific client
            socketio_instance.emit('tts_error', {'error': str(e)}, room=session_id)
        
        finally:
            # Clean up stream state
            if session_id in stream_tracker:
                del stream_tracker[session_id]

    @socketio.on('stop_tts')
    def handle_stop_tts():
        """Handle request to stop TTS streaming."""
        try:
            session_id = request.sid
            app.logger.info(f"TTS streaming stop requested for session {session_id}")
            
            # Mark stream for stopping
            if session_id in active_streams:
                active_streams[session_id]['should_stop'] = True
                app.logger.info(f"Marked stream for stopping: session {session_id}")
            
            emit('tts_stopped', {'status': 'stopped'})
        except Exception as e:
            app.logger.error(f"Error stopping TTS: {e}")
            emit('tts_error', {'error': str(e)})

    @socketio.on('client_heartbeat')
    def on_client_heartbeat(data):
        """Handle heartbeat from client."""
        session_id = request.sid
        app.logger.debug(f"Received heartbeat from client {session_id}, data: {data}")
        emit('server_heartbeat_ack', {'timestamp': data.get('timestamp')}, room=session_id) 