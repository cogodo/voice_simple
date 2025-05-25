"""
TTS WebSocket event handlers for streaming text-to-speech.
"""
import asyncio
import logging
import struct
from flask_socketio import emit
from flask import request
from services.voice_synthesis import my_processing_function_streaming

def register_tts_events(socketio, app):
    """Register TTS-related WebSocket events."""
    
    # Audio configuration for raw PCM streaming
    SAMPLE_RATE = 22050  # Match Cartesia output
    CHANNELS = 1
    FRAME_SIZE = int(0.02 * SAMPLE_RATE)  # 20ms frames = 441 samples
    
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
            
            # Start streaming task with session ID
            socketio.start_background_task(stream_tts_pcm, text, session_id, socketio, app)
            
        except Exception as e:
            app.logger.error(f"Error starting TTS: {e}")
            emit('tts_error', {'error': str(e)})

    def stream_tts_pcm(text, session_id, socketio_instance, app_instance):
        """Stream TTS audio as raw PCM frames."""
        try:
            app_instance.logger.info(f"Starting PCM-based TTS streaming for session {session_id}")
            
            # Signal start of streaming to specific client
            socketio_instance.emit('tts_started', {'status': 'streaming'}, room=session_id)
            
            frame_count = 0
            
            # Stream from Cartesia - frames are already correctly sized (882 bytes each)
            for frame_data in my_processing_function_streaming(text, app_instance.logger):
                # Send frame directly to specific client
                socketio_instance.emit('pcm_frame', list(frame_data), room=session_id)
                
                frame_count += 1
                
                # Log progress occasionally
                if frame_count % 50 == 0:  # Every second (50 * 20ms)
                    app_instance.logger.debug(f"Sent {frame_count} PCM frames to session {session_id}")
            
            # Signal completion to specific client
            socketio_instance.emit('tts_completed', {
                'status': 'completed',
                'frames_sent': frame_count,
                'duration_ms': frame_count * 20
            }, room=session_id)
            
            app_instance.logger.info(f"TTS streaming completed for session {session_id}: {frame_count} frames, {frame_count * 20}ms duration")
            
        except Exception as e:
            app_instance.logger.error(f"Error in TTS streaming for session {session_id}: {e}", exc_info=True)
            # Send error to specific client
            socketio_instance.emit('tts_error', {'error': str(e)}, room=session_id)

    @socketio.on('stop_tts')
    def handle_stop_tts():
        """Handle request to stop TTS streaming."""
        try:
            session_id = request.sid
            app.logger.info(f"TTS streaming stop requested for session {session_id}")
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