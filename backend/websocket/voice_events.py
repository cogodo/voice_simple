"""
Voice-related WebSocket event handlers for the Voice Agent backend.
Handles voice recording, transcription, and integration with conversation pipeline.
"""
from flask import request
from flask_socketio import emit
import base64
import io
import tempfile
import os
from services.whisper_handler import create_whisper_handler
from services.openai_handler import create_conversation_manager

# Global conversation manager for voice interactions
_voice_conversation_manager = None

def get_or_create_voice_conversation_manager(app_logger):
    """Get or create the voice conversation manager."""
    global _voice_conversation_manager
    if _voice_conversation_manager is None:
        try:
            _voice_conversation_manager = create_conversation_manager(app_logger)
            app_logger.info("Voice conversation manager created successfully")
        except Exception as e:
            app_logger.error(f"Failed to create voice conversation manager: {e}")
            return None
    return _voice_conversation_manager

def register_voice_events(socketio, app, voice_sessions):
    """Register voice-related WebSocket events."""
    
    @socketio.on('start_voice_recording')
    def handle_start_voice_recording(data=None):
        """Initialize voice recording session."""
        session_id = request.sid
        app.logger.info(f"Starting voice recording for session {session_id}")
        
        try:
            # Initialize voice session buffer
            voice_sessions[session_id] = {
                'audio_chunks': [],
                'is_recording': True,
                'total_audio_data': bytearray(),
                'whisper_handler': None
            }
            
            # Create Whisper handler for this session
            try:
                voice_sessions[session_id]['whisper_handler'] = create_whisper_handler(app.logger)
                app.logger.info("Whisper handler created successfully")
            except Exception as whisper_error:
                app.logger.error(f"Failed to create Whisper handler: {whisper_error}")
                emit('transcription_error', {'error': 'Voice transcription service unavailable'})
                return
            
            emit('voice_recording_started', {'status': 'Voice recording initialized'})
            app.logger.info("Voice recording session initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Error starting voice recording: {e}")
            emit('transcription_error', {'error': 'Failed to initialize voice recording'})

    @socketio.on('voice_chunk')
    def handle_voice_chunk(data):
        """
        Process incoming audio chunks for real-time or batch transcription.
        Expects data: {
            'audio_data': base64_encoded_audio_bytes,
            'chunk_id': string,
            'format': 'wav' | 'webm' | 'mp3' etc.
        }
        """
        session_id = request.sid
        
        if session_id not in voice_sessions:
            emit('transcription_error', {'error': 'Voice recording not initialized'})
            return
        
        if not voice_sessions[session_id]['is_recording']:
            emit('transcription_error', {'error': 'Voice recording not active'})
            return
        
        try:
            # Extract audio data
            audio_data_b64 = data.get('audio_data')
            chunk_id = data.get('chunk_id', 'unknown')
            audio_format = data.get('format', 'wav')
            
            if not audio_data_b64:
                emit('transcription_error', {'error': 'No audio data received'})
                return
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data_b64)
            
            app.logger.debug(f"Received voice chunk {chunk_id}: {len(audio_bytes)} bytes ({audio_format})")
            
            # Accumulate audio data
            voice_sessions[session_id]['audio_chunks'].append({
                'data': audio_bytes,
                'chunk_id': chunk_id,
                'format': audio_format
            })
            voice_sessions[session_id]['total_audio_data'].extend(audio_bytes)
            
            # Emit chunk received confirmation
            emit('voice_chunk_received', {
                'chunk_id': chunk_id,
                'total_chunks': len(voice_sessions[session_id]['audio_chunks']),
                'total_bytes': len(voice_sessions[session_id]['total_audio_data'])
            })
            
        except Exception as e:
            app.logger.error(f"Error processing voice chunk: {e}", exc_info=True)
            emit('transcription_error', {'error': f'Error processing audio chunk: {str(e)}'})

    @socketio.on('stop_voice_recording')
    def handle_stop_voice_recording(data=None):
        """Stop voice recording and process accumulated audio for transcription."""
        session_id = request.sid
        app.logger.info(f"Stopping voice recording for session {session_id}")
        
        if session_id not in voice_sessions:
            emit('transcription_error', {'error': 'Voice recording session not found'})
            return
        
        try:
            # Mark recording as stopped
            voice_sessions[session_id]['is_recording'] = False
            
            # Process accumulated audio
            emit('transcription_started', {'status': 'Processing speech...'})
            _process_complete_audio(session_id, app, voice_sessions)
            
        except Exception as e:
            app.logger.error(f"Error stopping voice recording: {e}")
            emit('transcription_error', {'error': 'Failed to stop voice recording'})

    @socketio.on('voice_data')
    def handle_voice_data(data):
        """
        Process complete audio file for transcription (legacy support).
        Expects data: {
            'audio_data': base64_encoded_audio_bytes,
            'format': 'wav' | 'webm' | 'mp3' etc.
        }
        """
        session_id = request.sid
        app.logger.info(f"Processing complete voice data for session {session_id}")
        
        try:
            # Extract audio data
            audio_data_b64 = data.get('audio_data')
            audio_format = data.get('format', 'wav')
            
            if not audio_data_b64:
                emit('transcription_error', {'error': 'No audio data received'})
                return
            
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data_b64)
            app.logger.info(f"Received complete audio: {len(audio_bytes)} bytes ({audio_format})")
            
            # Create temporary session for this audio
            temp_session_id = f"{session_id}_temp"
            voice_sessions[temp_session_id] = {
                'audio_chunks': [{'data': audio_bytes, 'format': audio_format}],
                'is_recording': False,
                'total_audio_data': bytearray(audio_bytes),
                'whisper_handler': create_whisper_handler(app.logger)
            }
            
            # Process audio
            emit('transcription_started', {'status': 'Processing speech...'})
            _process_complete_audio(temp_session_id, app, voice_sessions, audio_format)
            
            # Clean up temporary session
            if temp_session_id in voice_sessions:
                del voice_sessions[temp_session_id]
            
        except Exception as e:
            app.logger.error(f"Error processing voice data: {e}", exc_info=True)
            emit('transcription_error', {'error': f'Error processing audio: {str(e)}'})

    @socketio.on('cancel_voice_input')
    def handle_cancel_voice_input(data=None):
        """Cancel current voice input and clear audio buffer."""
        session_id = request.sid
        app.logger.info(f"Cancelling voice input for session {session_id}")
        
        try:
            if session_id in voice_sessions:
                # Clear audio buffer
                voice_sessions[session_id]['audio_chunks'] = []
                voice_sessions[session_id]['total_audio_data'] = bytearray()
                voice_sessions[session_id]['is_recording'] = False
                
                emit('voice_input_cancelled', {'status': 'Voice input cancelled'})
                app.logger.info("Voice input cancelled successfully")
            else:
                emit('voice_input_cancelled', {'status': 'No voice session to cancel'})
                
        except Exception as e:
            app.logger.error(f"Error cancelling voice input: {e}")
            emit('transcription_error', {'error': 'Failed to cancel voice input'})


def _process_complete_audio(session_id, app, voice_sessions, audio_format=None):
    """Process accumulated audio data for transcription."""
    try:
        if session_id not in voice_sessions:
            emit('transcription_error', {'error': 'Voice session not found'})
            return
        
        session = voice_sessions[session_id]
        total_audio = bytes(session['total_audio_data'])
        whisper_handler = session.get('whisper_handler')
        
        if not total_audio:
            emit('transcription_error', {'error': 'No audio data to process'})
            return
        
        if not whisper_handler:
            emit('transcription_error', {'error': 'Whisper handler not available'})
            return
        
        app.logger.info(f"Processing {len(total_audio)} bytes of audio for transcription")
        
        # Determine audio format
        if not audio_format:
            # Try to determine from first chunk
            if session['audio_chunks']:
                audio_format = session['audio_chunks'][0].get('format', 'wav')
            else:
                audio_format = 'wav'  # Default
        
        # Validate audio
        if not whisper_handler.validate_audio_format(total_audio):
            emit('transcription_error', {'error': 'Invalid audio format or corrupted audio data'})
            return
        
        # Get audio info for logging
        audio_info = whisper_handler.get_audio_info(total_audio, audio_format)
        app.logger.info(f"Audio info: {audio_info}")
        
        # Transcribe audio using Whisper
        app.logger.info("Sending audio to Whisper for transcription...")
        transcribed_text = whisper_handler.transcribe_audio(total_audio, audio_format)
        
        app.logger.info(f"Transcription complete: '{transcribed_text}'")
        
        # Emit transcription result
        emit('transcription_complete', {
            'text': transcribed_text,
            'audio_info': audio_info,
            'format': audio_format
        })
        
        # Automatically process as conversation input if text is not empty
        if transcribed_text.strip():
            app.logger.info("Processing transcribed text through conversation pipeline...")
            _process_transcribed_text_as_conversation(transcribed_text, app)
        else:
            app.logger.warning("Transcription resulted in empty text")
            emit('transcription_complete', {
                'text': '',
                'message': 'No speech detected in audio',
                'audio_info': audio_info
            })
        
        # Clean up audio buffer (but keep session for potential new recording)
        session['audio_chunks'] = []
        session['total_audio_data'] = bytearray()
        
    except Exception as e:
        app.logger.error(f"Error processing complete audio: {e}", exc_info=True)
        emit('transcription_error', {'error': f'Transcription failed: {str(e)}'})


def _process_transcribed_text_as_conversation(transcribed_text, app):
    """Process transcribed text through the conversation pipeline."""
    try:
        app.logger.info(f"=== PROCESSING TRANSCRIBED TEXT AS CONVERSATION ===")
        app.logger.info(f"Transcribed text: '{transcribed_text}'")
        
        # Get conversation manager
        conversation_manager = get_or_create_voice_conversation_manager(app.logger)
        if not conversation_manager:
            app.logger.error("Failed to get conversation manager")
            emit('conversation_error', {'error': 'Conversation manager not available'})
            return
        
        # Emit the transcribed text as a user message to frontend
        app.logger.info("Emitting user_message_from_voice...")
        emit('user_message_from_voice', {
            'message': transcribed_text,
            'source': 'voice',
            'timestamp': None
        })
        
        # Process conversation directly instead of using emit
        app.logger.info("Processing conversation directly...")
        
        # Add user message to conversation
        conversation_manager.add_user_message(transcribed_text)
        
        # Emit user message to frontend
        emit('user_message', {
            'role': 'user',
            'content': transcribed_text,
            'timestamp': conversation_manager.get_current_timestamp()
        })
        
        # Show AI thinking status
        app.logger.info("Emitting ai_thinking status...")
        emit('ai_thinking', {'status': 'AI is thinking...'})
        
        # Generate AI response
        app.logger.info("Generating AI response...")
        response = conversation_manager.get_response(transcribed_text)
        
        if response:
            app.logger.info(f"AI response generated: '{response[:100]}...'")
            
            # Add AI response to conversation
            conversation_manager.add_assistant_message(response)
            
            # Emit AI response
            app.logger.info("Emitting ai_response_complete...")
            emit('ai_response_complete', {
                'response': response,
                'role': 'assistant',
                'content': response,
                'timestamp': conversation_manager.get_current_timestamp()
            })
            
            # Automatically synthesize speech for the response
            app.logger.info("Triggering auto-TTS...")
            _trigger_auto_tts(response, app)
            
        else:
            app.logger.error("No response generated from AI")
            emit('conversation_error', {'error': 'Failed to generate AI response'})
        
    except Exception as e:
        app.logger.error(f"Error processing transcribed text as conversation: {e}", exc_info=True)
        emit('conversation_error', {'error': f'Failed to process voice message: {str(e)}'})


def _trigger_auto_tts(text, app):
    """Trigger automatic TTS synthesis for AI responses."""
    try:
        app.logger.info(f"Auto-triggering TTS for: '{text[:50]}...'")
        
        # Import here to avoid circular imports
        from services.voice_synthesis import my_processing_function_streaming
        
        # Start synthesis - use same format as TTS events
        emit('tts_started', {'status': 'streaming'})
        
        frame_count = 0
        
        # Stream audio chunks from Cartesia with optimized timing
        for audio_chunk in my_processing_function_streaming(text, app.logger):
            frame_count += 1
            
            app.logger.debug(f"Auto-TTS PCM frame {frame_count}: {len(audio_chunk)} bytes")
            
            # Use pcm_frame format to match TTS events handler
            emit('pcm_frame', list(audio_chunk))
            
        app.logger.info(f"Auto-TTS synthesis completed successfully. Sent {frame_count} PCM frames.")
        emit('tts_completed', {
            'status': 'completed', 
            'frames_sent': frame_count,
            'duration_ms': frame_count * 20
        })
            
    except Exception as e:
        app.logger.error(f"Error in auto-TTS synthesis: {e}", exc_info=True)
        emit('tts_error', {'error': f'Auto-TTS synthesis error: {str(e)}'}) 