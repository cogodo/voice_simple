"""
Text-to-Speech related WebSocket event handlers for the Voice Agent backend.
"""
from flask_socketio import emit
from services.voice_synthesis import my_processing_function_streaming


def register_tts_events(socketio, app):
    """Register TTS-related WebSocket events."""
    
    @socketio.on('synthesize_speech_streaming')
    def handle_synthesize_speech_streaming(data):
        """Handle streaming text-to-speech synthesis."""
        text = data.get('text', '').strip()
        voice_id = data.get('voice_id', None)  # Optional voice selection
        
        app.logger.info(f"Synthesizing speech for text: '{text[:100]}...'")
        
        if not text:
            emit('synthesis_error', {'error': 'No text provided for synthesis'})
            return
        
        try:
            # Start synthesis
            emit('synthesis_started', {'status': 'Generating speech...'})
            
            # Stream audio chunks from Cartesia
            def audio_chunk_callback(chunk_data):
                """Callback function to stream audio chunks to client."""
                emit('audio_chunk', {
                    'chunk_data': chunk_data,
                    'chunk_type': 'tts_audio'
                })
            
            # Call streaming synthesis with callback
            success = my_processing_function_streaming(
                text, 
                audio_chunk_callback,
                voice_id=voice_id
            )
            
            if success:
                app.logger.info("TTS synthesis completed successfully")
                emit('synthesis_complete', {'status': 'Speech synthesis completed'})
            else:
                app.logger.error("TTS synthesis failed")
                emit('synthesis_error', {'error': 'Speech synthesis failed'})
                
        except Exception as e:
            app.logger.error(f"Error in speech synthesis: {e}", exc_info=True)
            emit('synthesis_error', {'error': f'Synthesis error: {str(e)}'}) 