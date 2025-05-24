"""
Text-to-Speech related WebSocket event handlers for the Voice Agent backend.
"""
import base64
from flask_socketio import emit
from services.voice_synthesis import my_processing_function_streaming


def register_tts_events(socketio, app):
    """Register TTS-related WebSocket events."""
    
    @socketio.on('synthesize_speech_streaming')
    def handle_synthesize_speech_streaming(data):
        """Handle streaming text-to-speech synthesis."""
        text = data.get('text', '').strip()
        
        app.logger.info(f"Synthesizing speech for text: '{text[:100]}...'")
        
        if not text:
            emit('synthesis_error', {'error': 'No text provided for synthesis'})
            return
        
        try:
            # Start synthesis
            emit('tts_starting', {'text': text[:50], 'status': 'Generating speech...'})
            
            chunk_count = 0
            
            # Stream audio chunks from Cartesia
            for audio_chunk in my_processing_function_streaming(text, app.logger):
                chunk_count += 1
                
                # Convert audio chunk to base64 for transmission
                audio_chunk_b64 = base64.b64encode(audio_chunk).decode('utf-8')
                
                app.logger.debug(f"Streaming audio chunk {chunk_count}: {len(audio_chunk)} bytes")
                
                # Emit audio chunk to client
                emit('audio_chunk', {
                    'audio_chunk': list(audio_chunk),  # Convert bytes to list for JSON
                    'chunk_data': audio_chunk_b64,     # Base64 for easier handling
                    'chunk_type': 'tts_audio',
                    'chunk_number': chunk_count
                })
            
            app.logger.info(f"TTS synthesis completed successfully. Sent {chunk_count} audio chunks.")
            emit('tts_finished', {'status': 'Speech synthesis completed', 'total_chunks': chunk_count})
                
        except Exception as e:
            app.logger.error(f"Error in speech synthesis: {e}", exc_info=True)
            emit('tts_error', {'error': f'Synthesis error: {str(e)}'}) 