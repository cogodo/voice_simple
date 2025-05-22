from flask import Flask, render_template, request, jsonify
import os
from voice_thing import my_processing_function # Assuming voice_thing.py is in the same directory

# --- Flask App Setup ---
app = Flask(__name__)

# Set a secret key for session management (if you use sessions, not strictly needed for this example)
# app.secret_key = os.urandom(24) 

# --- Environment Variable Check (Optional but good practice) ---
CARTESIA_API_KEY = os.getenv("CARTESIA_API_KEY")
if not CARTESIA_API_KEY:
    print("WARNING: CARTESIA_API_KEY environment variable is not set. Voice generation will fail.")
    # You might want to handle this more gracefully in a real app, 
    # perhaps by disabling the voice feature or showing a clear error on the page.

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

# --- Main ---
if __name__ == '__main__':
    # Make sure debug is False in a production environment!
    # The host='0.0.0.0' makes it accessible from your network, not just localhost.
    app.run(debug=True, host='0.0.0.0', port=5000)
