"""
Voice-related WebSocket event handlers for the Voice Agent backend.
"""
from flask import request
from flask_socketio import emit
import base64
from services.whisper_handler import transcribe_audio, is_audio_valid, get_conversation_context


def register_voice_events(socketio, app, voice_sessions):
    """Register voice-related WebSocket events."""
    
    @socketio.on('start_voice_conversation')
    def handle_start_voice_conversation():
        """Initialize voice conversation mode."""
        session_id = request.sid
        app.logger.info(f"Starting voice conversation for session {session_id}")
        
        try:
            # Initialize voice session buffer
            voice_sessions[session_id] = {
                'audio_chunks': [],
                'is_recording': False,
                'total_audio_data': b''
            }
            
            emit('voice_conversation_ready', {'status': 'Voice conversation mode activated'})
            app.logger.info("Voice conversation initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Error starting voice conversation: {e}")
            emit('transcription_error', {'error': 'Failed to initialize voice conversation'})

    @socketio.on('audio_chunk')
    def handle_audio_chunk(data):
        """
        Process incoming audio chunks and accumulate for transcription.
        Expects data: {
            'audio_data': base64_encoded_audio_bytes,
            'is_final': boolean,
            'chunk_id': uuid,
            'format': 'webm' (or other format)
        }
        """
        session_id = request.sid
        
        if session_id not in voice_sessions:
            emit('transcription_error', {'error': 'Voice conversation not initialized'})
            return
        
        try:
            # Decode audio data from base64
            audio_data_b64 = data.get('audio_data')
            is_final = data.get('is_final', False)
            audio_format = data.get('format', 'webm')
            chunk_id = data.get('chunk_id', 'unknown')
            
            if not audio_data_b64:
                emit('transcription_error', {'error': 'No audio data received'})
                return
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data_b64)
            
            app.logger.debug(f"Received audio chunk {chunk_id}: {len(audio_bytes)} bytes, final={is_final}")
            
            # Accumulate audio data
            voice_sessions[session_id]['audio_chunks'].append(audio_bytes)
            voice_sessions[session_id]['total_audio_data'] += audio_bytes
            
            if is_final:
                # Process complete audio for transcription
                emit('transcription_started', {'status': 'Processing speech...'})
                _process_complete_audio(session_id, audio_format, app, voice_sessions)
            
        except Exception as e:
            app.logger.error(f"Error processing audio chunk: {e}", exc_info=True)
            emit('transcription_error', {'error': f'Error processing audio: {str(e)}'})

    @socketio.on('cancel_voice_input')
    def handle_cancel_voice_input():
        """Cancel current voice input and clear audio buffer."""
        session_id = request.sid
        app.logger.info(f"Cancelling voice input for session {session_id}")
        
        try:
            if session_id in voice_sessions:
                # Clear audio buffer
                voice_sessions[session_id]['audio_chunks'] = []
                voice_sessions[session_id]['total_audio_data'] = b''
                voice_sessions[session_id]['is_recording'] = False
                
                emit('voice_input_cancelled', {'status': 'Voice input cancelled'})
                app.logger.info("Voice input cancelled successfully")
            else:
                emit('voice_input_cancelled', {'status': 'No voice session to cancel'})
                
        except Exception as e:
            app.logger.error(f"Error cancelling voice input: {e}")
            emit('transcription_error', {'error': 'Failed to cancel voice input'})


def _process_complete_audio(session_id, audio_format, app, voice_sessions):
    """Process accumulated audio data for transcription."""
    from .conversation_events import _process_transcribed_text_as_conversation
    
    try:
        if session_id not in voice_sessions:
            emit('transcription_error', {'error': 'Voice session not found'})
            return
        
        total_audio = voice_sessions[session_id]['total_audio_data']
        
        if not total_audio:
            emit('transcription_error', {'error': 'No audio data to process'})
            return
        
        app.logger.info(f"Processing {len(total_audio)} bytes of audio for transcription")
        
        # Validate audio before processing
        if not is_audio_valid(total_audio):
            emit('transcription_error', {'error': 'Audio quality insufficient for transcription'})
            return
        
        # Get conversation context for better accuracy
        # This will need to be passed from the conversation manager
        conversation_context = ""
        
        # Transcribe audio using Whisper
        app.logger.info("Sending audio to Whisper for transcription...")
        transcription_result = transcribe_audio(
            total_audio, 
            conversation_context, 
            audio_format
        )
        
        transcribed_text = transcription_result['text']
        app.logger.info(f"Transcription complete: '{transcribed_text}'")
        
        # Emit transcription result
        emit('transcription_complete', {
            'text': transcribed_text,
            'duration': transcription_result.get('duration'),
            'confidence': transcription_result.get('confidence'),
            'language': transcription_result.get('language', 'en')
        })
        
        # Automatically process as conversation input if text is not empty
        if transcribed_text.strip():
            app.logger.info("Processing transcribed text through conversation pipeline...")
            _process_transcribed_text_as_conversation(transcribed_text)
        
        # Clean up audio buffer
        voice_sessions[session_id]['audio_chunks'] = []
        voice_sessions[session_id]['total_audio_data'] = b''
        
    except Exception as e:
        app.logger.error(f"Error processing complete audio: {e}", exc_info=True)
        emit('transcription_error', {'error': f'Transcription failed: {str(e)}'}) 