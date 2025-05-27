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
        app.logger.info('=== CLIENT CONNECTED ===')
        
        # Initialize conversation manager for this session
        try:
            app.logger.info("Attempting to create conversation manager...")
            conversation_manager = create_conversation_manager(app.logger)
            app.logger.info("Conversation manager initialized successfully")
            emit('conversation_ready', {'status': 'ready'})
        except Exception as e:
            app.logger.error(f"Failed to initialize conversation manager: {e}", exc_info=True)
            emit('conversation_error', {'error': 'Failed to initialize AI conversation system'})

    @socketio.on('disconnect')
    def handle_disconnect():
        app.logger.info('Client disconnected')

    @socketio.on('user_message')
    def handle_user_message(data):
        """Handle user message from frontend chat."""
        nonlocal conversation_manager
        
        if not conversation_manager:
            emit('conversation_error', {'error': 'Conversation manager not initialized'})
            return
        
        user_message = data.get('message', '').strip()
        app.logger.info(f"Processing user message: '{user_message}'")
        
        if not user_message:
            emit('conversation_error', {'error': 'Empty message received'})
            return
        
        try:
            # Add user message to conversation
            conversation_manager.add_user_message(user_message)
            
            # Show AI thinking status
            emit('ai_thinking', {'status': 'AI is thinking...'})
            
            # Generate AI response
            app.logger.info("Generating AI response...")
            response = conversation_manager.get_response(user_message)
            
            if response:
                app.logger.info(f"AI response generated: '{response[:100]}...'")
                
                # Add AI response to conversation
                conversation_manager.add_assistant_message(response)
                
                # Emit AI response back to frontend
                emit('ai_response', {
                    'message': response,
                    'response': response,
                    'role': 'assistant',
                    'timestamp': conversation_manager.get_current_timestamp()
                })
                
            else:
                app.logger.error("No response generated from AI")
                emit('conversation_error', {'error': 'Failed to generate AI response'})
                
        except Exception as e:
            app.logger.error(f"Error in conversation: {e}", exc_info=True)
            emit('conversation_error', {'error': f'Conversation error: {str(e)}'})

    @socketio.on('conversation_text_input')
    def handle_conversation_text_input(data):
        """Handle text input for AI conversation."""
        nonlocal conversation_manager
        
        app.logger.info(f"=== CONVERSATION_TEXT_INPUT HANDLER CALLED ===")
        app.logger.info(f"Data received: {data}")
        
        if not conversation_manager:
            app.logger.error("Conversation manager not initialized!")
            emit('conversation_error', {'error': 'Conversation manager not initialized'})
            return
        
        user_message = data.get('text', '').strip()
        app.logger.info(f"Processing conversation input: '{user_message}'")
        
        if not user_message:
            app.logger.error("Empty message received in conversation_text_input")
            emit('conversation_error', {'error': 'Empty message received'})
            return
        
        try:
            app.logger.info("Adding user message to conversation...")
            # Add user message to conversation
            conversation_manager.add_user_message(user_message)
            
            # Emit user message to frontend
            emit('user_message', {
                'role': 'user',
                'content': user_message,
                'timestamp': conversation_manager.get_current_timestamp()
            })
            
            # Show AI thinking status
            app.logger.info("Emitting ai_thinking status...")
            emit('ai_thinking', {'status': 'AI is thinking...'})
            
            # Generate AI response
            app.logger.info("Generating AI response...")
            response = conversation_manager.get_response(user_message)
            
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
        """Trigger automatic TTS synthesis for AI responses with proper timing."""
        try:
            app.logger.info(f"Auto-triggering TTS with timing control for: '{text[:50]}...'")
            
            # Import here to avoid circular imports
            from services.voice_synthesis import my_processing_function_streaming
            import time
            
            # Start synthesis - use same format as TTS events
            emit('tts_started', {'status': 'streaming'})
            
            # Pre-collect all frames for timing control
            app.logger.info("Pre-collecting frames for auto-TTS timing control...")
            audio_frames = []
            
            try:
                for audio_chunk in my_processing_function_streaming(text, app.logger):
                    audio_frames.append(audio_chunk)
                
                app.logger.info(f"Auto-TTS collected {len(audio_frames)} frames for timed streaming")
                
            except Exception as e:
                app.logger.error(f"Error collecting auto-TTS frames: {e}")
                emit('tts_error', {'error': f'Auto-TTS frame collection failed: {str(e)}'})
                return
            
            if not audio_frames:
                app.logger.warning("No audio frames collected for auto-TTS")
                emit('tts_error', {'error': 'No audio generated for auto-TTS'})
                return
            
            # Stream frames with real-time timing (20ms per frame)
            FRAME_DURATION_MS = 20
            start_time = time.time()
            
            app.logger.info(f"Starting auto-TTS real-time streaming: {len(audio_frames)} frames")
            
            for frame_index, audio_chunk in enumerate(audio_frames):
                # Calculate when this frame should be sent
                expected_time = start_time + (frame_index * FRAME_DURATION_MS / 1000.0)
                current_time = time.time()
                
                # Wait if we're ahead of schedule
                if current_time < expected_time:
                    sleep_time = expected_time - current_time
                    time.sleep(sleep_time)
                
                # Send frame with timing info
                emit('pcm_frame', list(audio_chunk))
                
                # Log progress occasionally
                if (frame_index + 1) % 50 == 0:
                    elapsed_time = time.time() - start_time
                    expected_elapsed = (frame_index + 1) * FRAME_DURATION_MS / 1000.0
                    timing_drift = elapsed_time - expected_elapsed
                    app.logger.debug(
                        f"Auto-TTS: Sent {frame_index + 1} frames, "
                        f"elapsed: {elapsed_time:.2f}s, drift: {timing_drift:.3f}s"
                    )
            
            # Calculate final timing metrics
            frames_sent = len(audio_frames)
            total_duration_ms = frames_sent * FRAME_DURATION_MS
            actual_duration = time.time() - start_time
            
            app.logger.info(f"Auto-TTS synthesis completed successfully. Sent {frames_sent} frames in {actual_duration:.2f}s (expected: {total_duration_ms/1000:.2f}s)")
            
            emit('tts_completed', {
                'status': 'completed', 
                'frames_sent': frames_sent,
                'duration_ms': total_duration_ms,
                'actual_duration_ms': int(actual_duration * 1000),
                'timing_accuracy': f"{((total_duration_ms/1000) / actual_duration * 100):.1f}%",
                'source': 'auto_tts'
            })
                
        except Exception as e:
            app.logger.error(f"Error in auto-TTS synthesis: {e}", exc_info=True)
            emit('tts_error', {'error': f'Auto-TTS synthesis error: {str(e)}'})
    
    return _process_transcribed_text_as_conversation 