"""
Conversation-related WebSocket event handlers for the Voice Agent backend.
"""
from flask_socketio import emit
from services.openai_handler import create_conversation_manager


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
                emit('ai_response', {
                    'role': 'assistant',
                    'content': response,
                    'timestamp': conversation_manager.get_current_timestamp()
                })
                
                # Automatically synthesize speech for the response
                emit('auto_synthesize_speech', {'text': response})
                
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
                emit('ai_response', {
                    'role': 'assistant',
                    'content': response,
                    'timestamp': conversation_manager.get_current_timestamp(),
                    'auto_speech': True  # Indicate this should auto-play speech
                })
                
                # Automatically synthesize and play speech for voice conversation
                emit('auto_synthesize_speech', {'text': response})
                
            else:
                app.logger.error("No response generated from AI for voice input")
                emit('conversation_error', {'error': 'Failed to generate AI response for voice input'})
                
        except Exception as e:
            app.logger.error(f"Error processing voice input as conversation: {e}", exc_info=True)
            emit('conversation_error', {'error': f'Voice conversation error: {str(e)}'})
    
    return _process_transcribed_text_as_conversation 