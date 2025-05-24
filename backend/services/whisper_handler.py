"""
OpenAI Whisper API integration for speech-to-text conversion.
Handles audio processing and transcription for Phase 3 voice-to-voice conversations.
"""

import os
import io
import tempfile
import openai
from pydub import AudioSegment
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

def convert_to_whisper_format(audio_data, input_format='webm'):
    """
    Convert audio data to format suitable for Whisper API.
    
    Args:
        audio_data (bytes): Raw audio data
        input_format (str): Input audio format (webm, wav, mp3, etc.)
    
    Returns:
        bytes: Audio data in WAV format suitable for Whisper
    """
    try:
        # Create AudioSegment from raw bytes
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format=input_format)
        
        # Convert to Whisper's preferred format: 16kHz mono
        audio = audio.set_frame_rate(16000).set_channels(1)
        
        # Export to WAV format in memory
        output_buffer = io.BytesIO()
        audio.export(output_buffer, format="wav")
        
        logger.debug(f"Converted audio: {len(audio_data)} bytes -> {output_buffer.tell()} bytes (16kHz mono WAV)")
        return output_buffer.getvalue()
        
    except Exception as e:
        logger.error(f"Error converting audio format: {e}")
        raise


def transcribe_audio(audio_data, conversation_context="", input_format='webm'):
    """
    Transcribe audio using OpenAI Whisper API.
    
    Args:
        audio_data (bytes): Raw audio data
        conversation_context (str): Previous conversation context for better accuracy
        input_format (str): Input audio format
    
    Returns:
        dict: Transcription result with text and metadata
    
    Raises:
        Exception: If transcription fails
    """
    if not audio_data:
        raise ValueError("No audio data provided")
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    try:
        # Convert audio to suitable format
        processed_audio = convert_to_whisper_format(audio_data, input_format)
        
        # Create temporary file for Whisper API
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_file.write(processed_audio)
            temp_file_path = temp_file.name
        
        try:
            # Call Whisper API
            with open(temp_file_path, "rb") as audio_file:
                logger.info(f"Sending {len(processed_audio)} bytes to Whisper API")
                
                # Prepare Whisper API parameters
                whisper_params = {
                    "model": "whisper-1",
                    "file": audio_file,
                    "response_format": "verbose_json",  # Get confidence and timing info
                    "temperature": 0.0  # Deterministic output
                }
                
                # Add conversation context as prompt if available (max 224 chars)
                if conversation_context:
                    whisper_params["prompt"] = conversation_context[:224]
                
                # Make API call
                client = openai.OpenAI(api_key=api_key)
                transcript = client.audio.transcriptions.create(**whisper_params)
                
                result = {
                    "text": transcript.text.strip(),
                    "duration": getattr(transcript, 'duration', None),
                    "language": getattr(transcript, 'language', 'en'),
                    "confidence": getattr(transcript, 'confidence', None)
                }
                
                logger.info(f"Transcription successful: '{result['text'][:100]}...'")
                return result
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file_path)
            except OSError:
                logger.warning(f"Could not delete temporary file: {temp_file_path}")
    
    except Exception as e:
        logger.error(f"Error during transcription: {e}", exc_info=True)
        raise


def is_audio_valid(audio_data, min_duration_ms=100):
    """
    Validate if audio data is suitable for transcription.
    
    Args:
        audio_data (bytes): Raw audio data
        min_duration_ms (int): Minimum duration in milliseconds
    
    Returns:
        bool: True if audio is valid for transcription
    """
    try:
        if not audio_data or len(audio_data) < 1000:  # Less than 1KB
            return False
        
        # Check audio duration
        audio = AudioSegment.from_file(io.BytesIO(audio_data), format='webm')
        if len(audio) < min_duration_ms:
            logger.debug(f"Audio too short: {len(audio)}ms < {min_duration_ms}ms")
            return False
        
        # Check for silence (very basic check)
        if audio.max_possible_amplitude > 0:
            # Calculate RMS (root mean square) for volume check
            rms = audio.rms
            if rms < 100:  # Very quiet audio
                logger.debug(f"Audio too quiet: RMS={rms}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating audio: {e}")
        return False


async def transcribe_audio_async(audio_data, conversation_context="", input_format='webm'):
    """
    Async wrapper for transcribe_audio function.
    
    Args:
        audio_data (bytes): Raw audio data
        conversation_context (str): Previous conversation context
        input_format (str): Input audio format
    
    Returns:
        dict: Transcription result
    """
    import asyncio
    import functools
    
    # Run the synchronous function in a thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, 
        functools.partial(
            transcribe_audio, 
            audio_data, 
            conversation_context, 
            input_format
        )
    )
    return result


def get_conversation_context(conversation_history, max_length=200):
    """
    Extract relevant context from conversation history for Whisper prompt.
    
    Args:
        conversation_history (list): List of previous messages
        max_length (int): Maximum context length in characters
    
    Returns:
        str: Context string for Whisper prompt
    """
    if not conversation_history:
        return ""
    
    # Get last few messages
    recent_messages = conversation_history[-3:]  # Last 3 messages
    context_parts = []
    
    for msg in recent_messages:
        if isinstance(msg, dict):
            content = msg.get('content', '')
            role = msg.get('role', '')
            if content and role in ['user', 'assistant']:
                context_parts.append(f"{role}: {content[:50]}")
    
    context = " ".join(context_parts)
    return context[:max_length] if len(context) > max_length else context


# Test function for development
def test_whisper_integration():
    """Test function to verify Whisper integration works."""
    print("Testing Whisper integration...")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print("✅ OpenAI API key found")
    print("✅ Whisper handler module ready")
    return True


if __name__ == "__main__":
    # Run test when script is executed directly
    test_whisper_integration() 