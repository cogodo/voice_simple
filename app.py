from flask import Flask, render_template, request, send_file, jsonify
from cartesia import Cartesia
from cartesia.tts import OutputFormat_Raw, TtsRequestIdSpecifier
import os
import io
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize Cartesia client
client = Cartesia(
    api_key=os.getenv("CARTESIA_API_KEY"),
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    try:
        # Generate audio from text
        audio_bytes = client.tts.bytes(
            model_id="sonic-2",
            transcript=text,
            voice={
                "mode": "id",
                "id": "694f9389-aac1-45b6-b726-9d9369183238",
            },
            language="en",
            output_format={
                "container": "raw",
                "sample_rate": 44100,
                "encoding": "pcm_f32le",
            },
        )
        
        # Create a temporary file to store the audio
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_path = temp_audio.name
            temp_audio.write(audio_bytes)
        
        return jsonify({
            'success': True,
            'audio_path': f'/audio/{os.path.basename(temp_path)}'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<filename>')
def get_audio(filename):
    temp_dir = tempfile.gettempdir()
    return send_file(os.path.join(temp_dir, filename), mimetype='audio/wav')

if __name__ == '__main__':
    app.run(debug=True) 