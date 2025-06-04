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

    @socketio.on('synthesize_speech_streaming')
    def handle_synthesize_speech_streaming(data):
        """Handle legacy synthesize_speech_streaming event (used by web test) - route to start_tts."""
        try:
            text = data.get('text', '')
            if not text:
                emit('tts_error', {'error': 'No text provided'})
                return
            
            app.logger.info(f"Received synthesize_speech_streaming (legacy), routing to start_tts: '{text[:50]}...'")
            
            # Route to the standard start_tts handler for consistency
            handle_start_tts(data)
            
        except Exception as e:
            app.logger.error(f"Error handling synthesize_speech_streaming: {e}")
            emit('tts_error', {'error': str(e)})

    def stream_tts_pcm_timed(text, session_id, socketio_instance, app_instance, stream_tracker):
        """Stream TTS audio as raw PCM frames in real-time."""
        try:
            app_instance.logger.info(f"Starting real-time PCM TTS streaming for session {session_id}")
            
            # Signal start of streaming to specific client
            socketio_instance.emit('tts_started', {'status': 'streaming'}, room=session_id)
            
            stream_state = stream_tracker[session_id]
            stream_state['start_time'] = time.time()
            
            # Stream frames in real-time as they're generated
            app_instance.logger.info("Starting real-time audio frame streaming...")
            frame_count = 0
            
            try:
                for frame_data in my_processing_function_streaming(text, app_instance.logger):
                    # Check if stream should stop
                    if stream_state['should_stop']:
                        app_instance.logger.info(f"Stream stopped at frame {frame_count} for session {session_id}")
                        break
                    
                    # Send frame immediately as it's generated
                    socketio_instance.emit('pcm_frame', list(frame_data), room=session_id)
                    frame_count += 1
                    stream_state['frames_sent'] = frame_count
                    
                    # Log progress occasionally (every 1 second worth of frames = 50 frames)
                    if frame_count % 50 == 0:
                        elapsed_time = time.time() - stream_state['start_time']
                        app_instance.logger.info(
                            f"Session {session_id}: Real-time streamed {frame_count} frames in {elapsed_time:.2f}s"
                        )
                    
                    # Add adaptive pacing based on client feedback
                    delay = get_adaptive_delay(session_id, stream_tracker)
                    time.sleep(delay)
                
            except Exception as e:
                app_instance.logger.error(f"Error during real-time streaming: {e}")
                socketio_instance.emit('tts_error', {'error': f'Real-time streaming failed: {str(e)}'}, room=session_id)
                return
            
            # Stream completed successfully
            actual_duration = time.time() - stream_state['start_time']
            
            # Signal completion to specific client
            socketio_instance.emit('tts_completed', {
                'status': 'completed',
                'frames_sent': frame_count,
                'actual_duration_ms': int(actual_duration * 1000),
                'message': f'Real-time streamed {frame_count} frames in {actual_duration:.2f}s'
            }, room=session_id)
            
            app_instance.logger.info(
                f"Real-time TTS streaming completed for session {session_id}: "
                f"{frame_count} frames in {actual_duration:.2f}s"
            )
            
        except Exception as e:
            app_instance.logger.error(f"Error in real-time TTS streaming for session {session_id}: {e}", exc_info=True)
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

    @socketio.on('audio_buffer_status')
    def handle_audio_buffer_status(data):
        """Handle audio buffer status feedback from client."""
        try:
            session_id = request.sid
            buffer_size = data.get('buffer_size', 0)
            underrun_count = data.get('underrun_count', 0)
            
            app.logger.debug(f"Client {session_id} buffer status: {buffer_size}ms, underruns: {underrun_count}")
            
            # Store client status for adaptive pacing
            if session_id in active_streams:
                active_streams[session_id]['client_buffer_size'] = buffer_size
                active_streams[session_id]['client_underrun_count'] = underrun_count
                
        except Exception as e:
            app.logger.error(f"Error handling audio buffer status: {e}")
    
    def get_adaptive_delay(session_id, stream_tracker):
        """Calculate adaptive delay based on client feedback."""
        if session_id not in stream_tracker:
            return 0.016  # Default 16ms (compensated for ~4ms processing overhead)
            
        client_buffer = stream_tracker[session_id].get('client_buffer_size', 60)
        
        # Adaptive pacing based on client buffer status (compensated for overhead)
        if client_buffer > 100:  # Client has large buffer - can send faster
            return 0.014  # 14ms - slightly faster
        elif client_buffer < 40:  # Client buffer low - slow down
            return 0.020  # 20ms - slower to let client catch up
        else:
            return 0.016  # Standard 16ms (compensated) 