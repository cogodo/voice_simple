from cartesia import Cartesia
import os
import io
import wave
import base64
import struct # Add this import
from flask import current_app # For logging
import socket # For catching socket.gaierror and direct getaddrinfo test
from urllib.parse import urlparse # For extracting hostname from URL
import logging # For standalone __main__ testing

# Basic logging config for when __main__ is run, Flask will have its own config
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    class MockFlaskLogger:
        def info(self, msg): logging.info(f"(MockFlaskLogger) {msg}")
        def error(self, msg, exc_info=None): logging.error(f"(MockFlaskLogger) {msg}", exc_info=exc_info)
        def warning(self, msg): logging.warning(f"(MockFlaskLogger) {msg}")
        def debug(self, msg): logging.debug(f"(MockFlaskLogger) {msg}")
    try:
        current_app.logger 
    except RuntimeError: 
        class MockCurrentApp: logger = MockFlaskLogger()
        current_app = MockCurrentApp()

def my_processing_function(text):
    current_app.logger.info("--- Checking Proxy Environment Variables ---")
    for proxy_var in ['HTTP_PROXY', 'HTTPS_PROXY', 'WS_PROXY', 'WSS_PROXY', 'NO_PROXY']:
        var_value = os.getenv(proxy_var)
        if var_value:
            current_app.logger.info(f"Proxy Env Var: {proxy_var} = {var_value}")
        else:
            current_app.logger.info(f"Proxy Env Var: {proxy_var} is NOT SET")
    current_app.logger.info("-----------------------------------------")

    api_key = os.getenv("CARTESIA_API_KEY")
    if not api_key:
        current_app.logger.error("CARTESIA_API_KEY not set in environment variables.")
        return "Error: CARTESIA_API_KEY environment variable not set. Please configure it."

    client = Cartesia(api_key=api_key)
    voice_id = "a0e99841-438c-4a64-b679-ae501e7d6091" 
    transcript = text
    sample_rate = 22050 

    audio_chunks = []
    # Determine the hostname from the Cartesia client's expected base URL if possible
    # This is usually 'api.cartesia.ai' for wss connections.
    # The actual WebSocket endpoint path is /tts/v1/websocket
    cartesia_hostname = "api.cartesia.ai" # Default assumption
    cartesia_wss_port = 443
    
    try:
        # --- Direct getaddrinfo test --- 
        current_app.logger.info(f"--- Performing direct DNS lookup for {cartesia_hostname}:{cartesia_wss_port} using socket.getaddrinfo (Python) ---")
        addr_info_results = socket.getaddrinfo(cartesia_hostname, cartesia_wss_port, 0, socket.SOCK_STREAM)
        current_app.logger.info(f"socket.getaddrinfo for {cartesia_hostname} SUCCEEDED. Results: {addr_info_results}")
    except socket.gaierror as e_direct_gaierror:
        current_app.logger.error(f"Direct socket.getaddrinfo for {cartesia_hostname} FAILED: {e_direct_gaierror}", exc_info=True)
        return f"Error: Python's direct DNS lookup (socket.getaddrinfo) for host '{cartesia_hostname}' failed. Details: {e_direct_gaierror}"
    except Exception as e_direct_other:
        current_app.logger.error(f"Direct socket.getaddrinfo for {cartesia_hostname} FAILED with unexpected error: {e_direct_other}", exc_info=True)
        return f"Error: Python's direct DNS lookup for host '{cartesia_hostname}' failed unexpectedly. Details: {e_direct_other}"
    current_app.logger.info("--- Direct DNS lookup test complete ---")

    hostname_to_resolve = "[unknown_hostname_before_ws_init]"
    target_ws_url = "[unknown_target_url_before_ws_init]"

    try:
        ws = client.tts.websocket() 
        
        target_ws_url = ws.ws_url # This should be something like wss://api.cartesia.ai/tts/v1/websocket
        current_app.logger.info(f"Cartesia client is targeting WebSocket URL: {target_ws_url}")
        parsed_url = urlparse(target_ws_url)
        hostname_to_resolve = parsed_url.hostname # Should also be api.cartesia.ai
        if hostname_to_resolve != cartesia_hostname:
            current_app.logger.warning(f"Mismatch! Direct test used '{cartesia_hostname}' but client targets '{hostname_to_resolve}'. This might be an issue.")
        
        current_app.logger.info(f"Attempting to connect to Cartesia WebSocket (hostname: '{hostname_to_resolve}') via client library...")
        ws.connect() 
        current_app.logger.info("Cartesia WebSocket connected successfully via client library.")
        current_app.logger.info("Sending TTS request and processing stream...")

        for i, output_item in enumerate(ws.send(
            model_id="sonic-2", 
            transcript=transcript,
            voice={"id": voice_id},
            stream=True, 
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le", 
                "sample_rate": sample_rate 
            },
        )):
            current_app.logger.info(f"Stream item {i}: type={type(output_item)}")
            try:
                current_app.logger.debug(f"Stream item {i} attributes: {dir(output_item)}")
            except Exception as log_e:
                current_app.logger.debug(f"Could not dir(output_item): {log_e}")

            if hasattr(output_item, 'audio') and output_item.audio is not None:
                current_app.logger.info(f"Stream item {i}: Received audio chunk of length {len(output_item.audio)}")
                audio_chunks.append(output_item.audio)
            else:
                current_app.logger.info(f"Stream item {i}: No audio data in this item or audio attribute is None.")

            if hasattr(output_item, 'status') and output_item.status is not None:
                current_app.logger.info(f"Stream item {i}: Status present - Code: {getattr(output_item.status, 'code', 'N/A')}, Message: {getattr(output_item.status, 'message', 'N/A')}")
            elif hasattr(output_item, 'event_type') and output_item.event_type is not None: 
                 current_app.logger.info(f"Stream item {i}: Event type present - {output_item.event_type}")

        current_app.logger.info("Finished iterating through ws.send() stream.")
        ws.close()
        current_app.logger.info("Cartesia WebSocket closed after streaming.")

    except socket.gaierror as e:
        current_app.logger.error(f"Network DNS Resolution Error (socket.gaierror) during client.ws.connect(): {e}. Target URL '{target_ws_url}' (hostname: '{hostname_to_resolve}')", exc_info=True)
        return f"Error: Network DNS resolution failed for host '{hostname_to_resolve}' when using client library. Details: {e}"
    except RuntimeError as e:
        current_app.logger.error(f"RuntimeError during client.ws.connect() or operation (hostname: '{hostname_to_resolve}'): {e}", exc_info=True)
        if "getaddrinfo failed" in str(e):
             return f"Error: Network connection failed for host '{hostname_to_resolve}' (RuntimeError containing getaddrinfo). Check DNS/firewall. Details: {e}"
        return f"Error: WebSocket connection or operation failed: {e}"
    except Exception as e:
        current_app.logger.error(f"An unexpected error occurred (hostname: '{hostname_to_resolve}'): {e}", exc_info=True)
        return f"Error: An unexpected error occurred while trying to get audio from Cartesia: {e}"

    if not audio_chunks:
        current_app.logger.warning("No audio chunks received from Cartesia. The audio_chunks list is empty.")
        return "Error: No audio data was received from the voice synthesis service."

    current_app.logger.info(f"Total audio chunks received: {len(audio_chunks)}. Concatenating...")
    full_audio_bytes_f32le = b"".join(audio_chunks)
    current_app.logger.info(f"Total concatenated float32 audio bytes: {len(full_audio_bytes_f32le)}.")

    if len(full_audio_bytes_f32le) == 0:
        current_app.logger.warning("Concatenated audio data is empty. Cannot create WAV.")
        return "Error: Received empty audio stream."

    # Convert float32 little-endian to int16 little-endian
    current_app.logger.info("Converting float32 audio to int16...")
    num_samples = len(full_audio_bytes_f32le) // 4
    full_audio_bytes_s16le = bytearray(num_samples * 2)
    for i in range(num_samples):
        float_val = struct.unpack_from('<f', full_audio_bytes_f32le, i * 4)[0]
        int_val = int(max(-1.0, min(1.0, float_val)) * 32767.0)
        struct.pack_into('<h', full_audio_bytes_s16le, i * 2, int_val)
    current_app.logger.info(f"Total concatenated int16 audio bytes: {len(full_audio_bytes_s16le)}.")

    output_filename = "generated_speech.wav"
    current_app.logger.info(f"Attempting to save audio to server file: {output_filename}")

    try:
        with wave.open(output_filename, "wb") as wf_file:
            wf_file.setnchannels(1)  
            wf_file.setsampwidth(2)  # Changed from 4 to 2 for int16
            wf_file.setframerate(sample_rate)
            wf_file.writeframes(full_audio_bytes_s16le)
        current_app.logger.info(f"Successfully saved audio to {output_filename} on the server.")

        current_app.logger.info(f"Creating WAV in memory for base64 encoding. Total int16 bytes: {len(full_audio_bytes_s16le)}, Sample rate: {sample_rate}")
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf_mem:
            wf_mem.setnchannels(1)  
            wf_mem.setsampwidth(2)  # Changed from 4 to 2 for int16
            wf_mem.setframerate(sample_rate)
            wf_mem.writeframes(full_audio_bytes_s16le) 
        
        wav_buffer.seek(0)
        wav_bytes_for_uri = wav_buffer.read()
        
        base64_audio = base64.b64encode(wav_bytes_for_uri).decode('utf-8')
        data_uri = f"data:audio/wav;base64,{base64_audio}"
        current_app.logger.info(f"Successfully created audio data URI (length: {len(data_uri)}).")
        return data_uri

    except Exception as e:
        current_app.logger.error(f"Error saving WAV file to disk or during base64 encoding: {e}", exc_info=True)
        return f"Error: Failed to process or save audio data: {e}"

if __name__ == "__main__":
    logging.info("Starting direct test of my_processing_function...")
    api_key_exists = os.getenv("CARTESIA_API_KEY")
    if not api_key_exists:
        logging.critical("CRITICAL: CARTESIA_API_KEY environment variable is not set. This test cannot run.")
    else:
        logging.info(f"CARTESIA_API_KEY is set. Proceeding with test call using text 'Hello from direct test'")
        result = my_processing_function("Hello from direct test") 
        
        if isinstance(result, str) and result.startswith("data:audio/wav;base64,"):
            logging.info(f"Generated data URI successfully (first 100 chars): {result[:100]}...")
            if os.path.exists("generated_speech.wav"):
                logging.info("File 'generated_speech.wav' was also created successfully on the server.")
            else:
                logging.warning("File 'generated_speech.wav' was NOT created on the server during direct test.")
        else:
            logging.error(f"Error or unexpected result in direct test: {result}")
