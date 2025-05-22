from flask import Flask, render_template, request, jsonify
import os
from flask_socketio import SocketIO, emit
from voice_thing import my_processing_function, my_processing_function_streaming
from openai_handler import create_conversation_manager

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Environment Variable Check ---
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not CARTESIA_API_KEY:
    app.logger.warning("WARNING: CARTESIA_API_KEY environment variable is not set. Voice generation will fail.")
if not OPENAI_API_KEY:
    app.logger.warning("WARNING: OPENAI_API_KEY environment variable is not set. LLM calls will fail.")

# Global conversation manager (in production, you'd want per-session managers)
conversation_manager = None

# --- Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html')

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    global conversation_manager
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

@socketio.on('synthesize_speech_streaming')
def handle_synthesize_speech_streaming(data):
    """
    Receives text from client, calls streaming TTS, and streams audio chunks back.
    Expects data: {"text": "your text here"}
    Emits: 'audio_chunk' with {'audio_chunk': binary_data}
           'tts_error' with {'error': message}
           'tts_finished' when done
    """
    text_to_speak = data.get('text')
    if not text_to_speak:
        emit('tts_error', {'error': 'No text provided'})
        return

    app.logger.info(f"Received request to synthesize and stream: '{text_to_speak}'")
    try:
        for audio_chunk_data in my_processing_function_streaming(text_to_speak, app.logger):
            emit('audio_chunk', {'audio_chunk': audio_chunk_data})
        emit('tts_finished')
        app.logger.info("Finished streaming TTS audio.")
    except Exception as e:
        app.logger.error(f"Error during streaming TTS: {e}", exc_info=True)
        emit('tts_error', {'error': str(e)})

@socketio.on('conversation_text_input')
def handle_conversation_text_input(data):
    """
    Handle text input for conversation with AI.
    This will get OpenAI response and then stream it as TTS.
    Expects data: {"text": "user's text input"}
    """
    global conversation_manager
    
    user_text = data.get('text')
    if not user_text:
        emit('conversation_error', {'error': 'No text provided'})
        return

    if not conversation_manager:
        # Try to initialize if it doesn't exist
        try:
            conversation_manager = create_conversation_manager(app.logger)
        except Exception as e:
            emit('conversation_error', {'error': 'Conversation manager not available'})
            return

    app.logger.info(f"Processing conversation input: '{user_text[:50]}...'")
    
    try:
        # Get streaming response from OpenAI
        app.logger.info("Getting streaming response from OpenAI...")
        emit('ai_thinking', {'status': 'AI is thinking...'})
        
        full_ai_response = ""
        for text_chunk in conversation_manager.get_streaming_response(user_text):
            full_ai_response += text_chunk
            # Emit the text chunk to frontend for display (optional)
            emit('ai_text_chunk', {'chunk': text_chunk})
        
        app.logger.info(f"Complete AI response received: '{full_ai_response[:100]}...'")
        emit('ai_response_complete', {'response': full_ai_response})
        
        # Now convert the complete AI response to speech
        if full_ai_response:
            app.logger.info("Starting TTS for AI response...")
            emit('tts_starting', {'text': full_ai_response})
            
            for audio_chunk_data in my_processing_function_streaming(full_ai_response, app.logger):
                emit('audio_chunk', {'audio_chunk': audio_chunk_data})
            
            emit('tts_finished')
            app.logger.info("Conversation turn complete.")
        
    except Exception as e:
        app.logger.error(f"Error during conversation processing: {e}", exc_info=True)
        emit('conversation_error', {'error': f'Error processing conversation: {str(e)}'})

@socketio.on('clear_conversation')
def handle_clear_conversation():
    """Clear the conversation history."""
    global conversation_manager
    
    if conversation_manager:
        conversation_manager.clear_conversation()
        app.logger.info("Conversation history cleared")
        emit('conversation_cleared', {'status': 'Conversation history cleared'})
    else:
        emit('conversation_error', {'error': 'No conversation to clear'})

# --- Main ---
if __name__ == '__main__':
    app.logger.info("Starting Flask-SocketIO server...")
    # Set logging level to DEBUG to see streaming details
    import logging
    logging.getLogger('voice_thing').setLevel(logging.DEBUG)
    logging.getLogger('openai_handler').setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    # host='0.0.0.0' makes it accessible from your network.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)