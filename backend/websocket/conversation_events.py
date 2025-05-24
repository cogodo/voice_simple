"""
Conversation-related WebSocket event handlers for the Voice Agent backend.
"""
from flask_socketio import emit
from services.openai_handler import create_conversation_manager
import time


def register_conversation_events(socketio, app):
    """Register conversation-related WebSocket events."""
    
    # Global conversation manager (in production, you'd want per-session managers)
    conversation_manager = None
    
    @socketio.on('connect')
    def handle_connect():
        nonlocal conversation_manager
        app.logger.info('Client connected')
        
        # Initialize conversation manager for this session
        try:
            conversation_manager = create_conversation_manager(app.logger)
            app.logger.info("Conversation manager initialized successfully")
            emit('conversation_ready', {'status': 'ready'})
        except Exception as e:
            app.logger.error(f"Failed to initialize conversation manager: {e}")
            emit('conversation_error', {'error': 'Failed to initialize AI conversation system'})

    @socketio.on('disconnect')
    def handle_disconnect():
        app.logger.info('Client disconnected')

    @socketio.on('conversation_text_input')
    def handle_conversation_text_input(data):
        """Handle text input for AI conversation."""
        nonlocal conversation_manager
        
        if not conversation_manager:
            emit('conversation_error', {'error': 'Conversation manager not initialized'})
            return
        
        user_message = data.get('text', '').strip()
        app.logger.info(f"Processing conversation input: '{user_message}'")
        
        if not user_message:
            emit('conversation_error', {'error': 'Empty message received'})
            return
        
        try:
            # Add user message to conversation
            conversation_manager.add_user_message(user_message)
            
            # Emit user message to frontend
            emit('user_message', {
                'role': 'user',
                'content': user_message,
                'timestamp': conversation_manager.get_current_timestamp()
            })
            
            # Show AI thinking status
            emit('ai_thinking', {'status': 'AI is thinking...'})
            
            # Generate AI response
            app.logger.info("Generating AI response...")
            response = conversation_manager.get_response(user_message)
            
            if response:
                app.logger.info(f"AI response generated: '{response[:100]}...'")
                
                # Add AI response to conversation
                conversation_manager.add_assistant_message(response)
                
                # Emit AI response
                emit('ai_response_complete', {
                    'response': response,
                    'role': 'assistant',
                    'content': response,
                    'timestamp': conversation_manager.get_current_timestamp()
                })
                
                # Automatically synthesize speech for the response
                _trigger_auto_tts(response, app)
                
            else:
                app.logger.error("No response generated from AI")
                emit('conversation_error', {'error': 'Failed to generate AI response'})
                
        except Exception as e:
            app.logger.error(f"Error in conversation: {e}", exc_info=True)
            emit('conversation_error', {'error': f'Conversation error: {str(e)}'})

    @socketio.on('clear_conversation')
    def handle_clear_conversation():
        """Clear the conversation history."""
        nonlocal conversation_manager
        
        try:
            if conversation_manager:
                conversation_manager.clear_conversation()
                app.logger.info("Conversation history cleared")
                emit('conversation_cleared', {'status': 'Conversation history cleared'})
            else:
                emit('conversation_error', {'error': 'No conversation to clear'})
                
        except Exception as e:
            app.logger.error(f"Error clearing conversation: {e}")
            emit('conversation_error', {'error': 'Failed to clear conversation'})

    def _process_transcribed_text_as_conversation(transcribed_text):
        """Process transcribed text through the conversation pipeline."""
        nonlocal conversation_manager
        
        if not conversation_manager:
            emit('conversation_error', {'error': 'Conversation manager not available'})
            return
        
        try:
            # Add user message (from voice) to conversation
            conversation_manager.add_user_message(transcribed_text)
            
            # Emit user message to frontend
            emit('user_message', {
                'role': 'user',
                'content': transcribed_text,
                'timestamp': conversation_manager.get_current_timestamp(),
                'source': 'voice'  # Indicate this came from voice input
            })
            
            # Show AI thinking status
            emit('ai_thinking', {'status': 'AI is thinking...'})
            
            # Generate AI response
            app.logger.info("Generating AI response for voice input...")
            response = conversation_manager.get_response(transcribed_text)
            
            if response:
                app.logger.info(f"AI response generated for voice: '{response[:100]}...'")
                
                # Add AI response to conversation
                conversation_manager.add_assistant_message(response)
                
                # Emit AI response
                emit('ai_response_complete', {
                    'response': response,
                    'role': 'assistant',
                    'content': response,
                    'timestamp': conversation_manager.get_current_timestamp()
                })
                
                # Automatically synthesize and play speech for voice conversation
                _trigger_auto_tts(response, app)
                
            else:
                app.logger.error("No response generated from AI for voice input")
                emit('conversation_error', {'error': 'Failed to generate AI response for voice input'})
                
        except Exception as e:
            app.logger.error(f"Error processing voice input as conversation: {e}", exc_info=True)
            emit('conversation_error', {'error': f'Voice conversation error: {str(e)}'})
    
    def _trigger_auto_tts(text, app):
        """Trigger automatic TTS synthesis for AI responses."""
        try:
            app.logger.info(f"Auto-triggering TTS for: '{text[:50]}...'")
            
            # Import here to avoid circular imports
            from services.voice_synthesis import my_processing_function_streaming
            
            # Start synthesis
            emit('tts_starting', {'text': text[:50], 'status': 'Generating speech...'})
            
            chunk_count = 0
            start_time = time.time()
            
            # Stream audio chunks from Cartesia with optimized timing
            for audio_chunk in my_processing_function_streaming(text, app.logger):
                chunk_count += 1
                
                app.logger.debug(f"Auto-TTS audio chunk {chunk_count}: {len(audio_chunk)} bytes")
                
                # Send only the list format for better performance (remove base64 overhead)
                emit('audio_chunk', {
                    'audio_chunk': list(audio_chunk),
                    'chunk_type': 'tts_audio',
                    'chunk_number': chunk_count,
                    'timestamp': time.time() - start_time  # Add timing info for debugging
                })
                
                # Add small server-side delay for consistent timing
                time.sleep(0.001)  # 1ms delay to prevent overwhelming client
            
            total_time = time.time() - start_time
            app.logger.info(f"Auto-TTS synthesis completed successfully. Sent {chunk_count} audio chunks in {total_time:.2f}s.")
            emit('tts_finished', {
                'status': 'Speech synthesis completed', 
                'total_chunks': chunk_count,
                'total_time': total_time
            })
                
        except Exception as e:
            app.logger.error(f"Error in auto-TTS synthesis: {e}", exc_info=True)
            emit('tts_error', {'error': f'Auto-TTS synthesis error: {str(e)}'})
    
    return _process_transcribed_text_as_conversation 