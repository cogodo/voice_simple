from flask import Flask, render_template, request, jsonify
import os
from flask_socketio import SocketIO, emit
from voice_thing import my_processing_function, my_processing_function_streaming # Assuming voice_thing.py is in the same directory

# --- Flask App Setup ---
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24) # SocketIO needs a secret key
socketio = SocketIO(app, cors_allowed_origins="*") # Allow all origins for simplicity in dev

# --- Environment Variable Check (Optional but good practice) ---
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") # For later
if not CARTESIA_API_KEY:
    print("WARNING: CARTESIA_API_KEY environment variable is not set. Voice generation will fail.")
    # You might want to handle this more gracefully in a real app, 
    # perhaps by disabling the voice feature or showing a clear error on the page.
if not OPENAI_API_KEY:
    app.logger.warning("WARNING: OPENAI_API_KEY environment variable is not set. LLM calls will fail later.")

# --- Routes ---
@app.route('/')
def index():
    """Serves the main HTML page."""
    return render_template('index.html') # We'll create this HTML file next

@app.route('/generate-audio', methods=['POST'])
def handle_generate_audio():
    """
    Handles the AJAX request to generate audio.
    Expects JSON: {"text": "your text here"}
    Returns JSON: {"audioDataUri": "data:..."} or {"error": "message"}
    """
    if not request.is_json:
        return jsonify({"error": "Invalid request: Content-Type must be application/json"}), 415

    data = request.get_json()
    text_to_speak = data.get('text')

    if not text_to_speak:
        return jsonify({"error": "No text provided in the request body"}), 400

    app.logger.info(f"Received request to generate audio for text: '{text_to_speak}'")

    # Call your existing processing function from voice_thing.py
    result_uri_or_error = my_processing_function(text_to_speak)

    if isinstance(result_uri_or_error, str) and result_uri_or_error.startswith("data:audio/wav;base64,"):
        app.logger.info("Successfully generated audio data URI.")
        return jsonify({"audioDataUri": result_uri_or_error})
    else:
        # my_processing_function returned an error message
        app.logger.error(f"Error from my_processing_function: {result_uri_or_error}")
        return jsonify({"error": result_uri_or_error}), 500

# --- SocketIO Event Handlers ---
@socketio.on('connect')
def handle_connect():
    app.logger.info('Client connected')

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
        # This will be a generator function
        for audio_chunk_data in my_processing_function_streaming(text_to_speak, app.logger):
            emit('audio_chunk', {'audio_chunk': audio_chunk_data})
        emit('tts_finished') # Signal end of stream
        app.logger.info("Finished streaming TTS audio.")
    except Exception as e:
        app.logger.error(f"Error during streaming TTS: {e}", exc_info=True)
        emit('tts_error', {'error': str(e)})

# --- Main ---
if __name__ == '__main__':
    app.logger.info("Starting Flask-SocketIO server...")
    # Set logging level to DEBUG to see streaming details
    import logging
    logging.getLogger('voice_thing').setLevel(logging.DEBUG)
    app.logger.setLevel(logging.DEBUG)
    # host='0.0.0.0' makes it accessible from your network.
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
